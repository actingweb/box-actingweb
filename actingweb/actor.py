from db import db
import datetime
import time
import base64
import property
import urllib
from google.appengine.api import urlfetch
from google.appengine.ext import deferred
import json
import config
import trust
import subscription
import logging
import peer

__all__ = [
    'actor',
]


def getPeerInfo(url):
    """Contacts an another actor over http/s to retrieve meta information."""
    try:
        logging.debug('Getting peer info at url(' + url + ')')
        response = urlfetch.fetch(url=url + '/meta',
                                  method=urlfetch.GET
                                  )
        res = {
            "last_response_code": response.status_code,
            "last_response_message": response.content,
            "data": json.loads(response.content),
        }
        logging.debug('Got peer info from url(' + url +
                      ') with body(' + response.content + ')')
    except:
        res = {
            "last_response_code": 500,
        }
    return res


class actor():

    def get(self, id):
        """Retrieves an actor from db or initialises if does not exist."""
        result = db.Actor.query(db.Actor.id == id).get(use_cache=False)
        if result:
            self.id = id
            self.creator = result.creator
            self.passphrase = result.passphrase
        else:
            self.id = None
            self.creator = None
            self.passphrase = None

    def get_from_property(self, name='oauthId', value=None):
        """ Initialise an actor by matching on a stored property.

        Use with caution as the property's value de-facto becomes
        a security token. If multiple properties are found with the
        same value, no actor will be initialised.
        Also note that this is a costly operation as all properties
        of this type will be retrieved and proceessed.
        """
        prop = property.property(name=name, value=value)
        if not prop.actorId:
            self.id = None
            self.creator = None
            self.passphrase = None
        self.get(prop.actorId)  

    def create(self, url, creator, passphrase):
        """"Creates a new actor and persists it to db."""
        seed = url
        now = datetime.datetime.now()
        seed += now.strftime("%Y%m%dT%H%M%S%f")
        if len(creator) > 0:
            self.creator = creator
        else:
            self.creator = "creator"

        Config = config.config()
        if passphrase and len(passphrase) > 0:
            self.passphrase = passphrase
        else:
            self.passphrase = Config.newToken()
        self.id = Config.newUUID(seed)
        actor = db.Actor(creator=self.creator,
                         passphrase=self.passphrase,
                         id=self.id)
        actor.put(use_cache=False)

    def delete(self):
        """Deletes an actor and cleans up all relevant stored data in db."""
        properties = db.Property.query(db.Property.id == self.id).fetch(use_cache=False)
        for prop in properties:
            prop.key.delete(use_cache=False)
        diffs = db.SubscriptionDiff.query(
            db.SubscriptionDiff.id == self.id).fetch(use_cache=False)
        for diff in diffs:
            diff.key.delete(use_cache=False)
        subs = db.Subscription.query(db.Subscription.id == self.id).fetch(use_cache=False)
        for sub in subs:
            self.deleteRemoteSubscription(peerid=sub.peerid, subid=sub.subid)
            sub.key.delete(use_cache=False)
        relationships = db.Trust.query(db.Trust.id == self.id).fetch(use_cache=False)
        for rel in relationships:
            self.deleteReciprocalTrust(peerid=rel.peerid, deletePeer=True)
            rel.key.delete(use_cache=False)
        result = db.Actor.query(db.Actor.id == self.id).get(use_cache=False)
        if result:
            result.key.delete(use_cache=False)

    def setProperty(self, name, value):
        """Sets an actor's property name to value."""
        prop = property.property(self, name)
        prop.set(value)

    def getProperty(self, name):
        """Retrieves a property name."""
        prop = property.property(self, name)
        return prop

    def deleteProperty(self, name):
        """Deletes a property name."""
        prop = property.property(self, name)
        if prop:
            prop.delete()

    def getProperties(self):
        """Retrieves properties from db."""
        properties = db.Property.query(db.Property.id == self.id).fetch(use_cache=False)
        return properties

    def deletePeerTrustee(self, shorttype=None, peerid=None):
        if not peerid and not shorttype:
            return False
        Config = config.config()
        if shorttype and not Config.actors[shorttype]:
            logging.error('Got a request to delete an unknown actor type(' + shorttype + ')')
            return False
        if peerid:
            new_peer = peer.peerTrustee(actor=self, peerid=peerid)
            if not new_peer.peer:
                return False
        elif shorttype:
            new_peer = peer.peerTrustee(actor=self, shorttype=shorttype)
            if not new_peer.peer:
                return False
        logging.debug(
            'Deleting peer actor at baseuri(' + new_peer.baseuri + ')')
        headers = {'Authorization': 'Basic ' +
                   base64.b64encode('trustee:' + new_peer.passphrase),
                   }
        try:
            response = urlfetch.fetch(url=new_peer.baseuri,
                                      method=urlfetch.DELETE,
                                      headers=headers
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            logging.debug('Not able to delete peer actor remotely')
            self.last_response_code = 408
            return False
        if response.status_code < 200 or response.status_code > 299:
            logging.debug('Not able to delete peer actor remotely')
            return False
        # Delete trust, peer is already deleted remotely
        if not self.deleteReciprocalTrust(peerid=new_peer.peerid, deletePeer=False):
            logging.debug('Not able to delete peer actor trust in db')
        if not new_peer.delete():
            logging.debug('Not able to delete peer actor in db')
            return False
        return True

    def getPeerTrustee(self, shorttype=None, peerid=None):
        """ Get a peer, either existing or create it as trustee 

        Will retrieve an existing peer or create a new and establish trust.
        If no trust exists, a new trust will be established.
        Use either peerid to target a specific known peer, or shorttype to
        allow creation of a new peer if none exists
        """
        if not peerid and not shorttype:
            return None
        Config = config.config()
        if shorttype and not Config.actors[shorttype]:
            logging.error('Got a request to create an unknown actor type(' + shorttype + ')')
            return None
        if peerid:
            new_peer = peer.peerTrustee(actor=self, peerid=peerid)
        else:
            new_peer = peer.peerTrustee(actor=self, shorttype=shorttype)
        if new_peer.peer:
            logging.debug('Found peer in getPeer, now checking existing trust...')
            new_trust = trust.trust(id=self.id, peerid=new_peer.peerid)
            if new_trust.trust:
                return new_peer
            logging.debug('Did not find existing trust, will create a new one')
        factory = Config.actors[shorttype]['factory']
        # If peer did not exist, create it as trustee
        if not new_peer.peer:
            if len(factory) == 0:
                logging.error('Peer actor of shorttype(' + 
                            shorttype + ') does not have factory set.')
            new_peer = peer.peerTrustee(actor=self)
            params = {
                'creator': 'trustee',
                'trustee_root': Config.root + self.id
            }
            data = json.dumps(params)
            logging.debug(
                'Creating peer actor at factory(' + factory + ') with data(' +
                str(data) + ')')
            try:
                response = urlfetch.fetch(url=factory,
                                        method=urlfetch.POST,
                                        payload=data
                                        )
                self.last_response_code = response.status_code
                self.last_response_message = response.content
            except:
                logging.debug('Not able to create new peer actor')
                self.last_response_code = 408
            logging.debug('Create peer actor POST response:' + response.content)
            if response.status_code < 200 or response.status_code > 299:
                return None
            try:
                data = json.loads(response.content)
            except:
                logging.warn("Not able to parse response when creating peer at factory(" + 
                            factory + ")")
                return None
            if 'Location' in response.headers:
                baseuri = response.headers['Location']
            res = getPeerInfo(baseuri)
            if not res or res["last_response_code"] < 200 or res["last_response_code"] >= 300:
                return None
            info = res["data"]
            if not info["id"] or not info["type"] or len(info["type"]) == 0:
                logging.info(
                    "Received invalid peer info when trying to create peer actor at: " + factory)
                return None
            if not new_peer.create(peerid=info["id"], baseuri=baseuri, 
                                type=info["type"], passphrase=data["passphrase"]):
                logging.error('Failed to create in db new peer actor(' + 
                            peer["id"] + ') at ' + baseuri)
                return None
        # Now peer exists, create trust
        new_trust = self.createReciprocalTrust(
                        url=new_peer.baseuri,
                        secret=Config.newToken(),
                        desc='Trust from trustee to ' + shorttype,
                        relationship=Config.actors[shorttype]['relationship']
                        )
        if not new_trust:
            logging.warn("Not able to establish trust relationship with peer at factory(" +
                         factory + ")")
        else:
            # Approve the relationship
            params = {
                'approved': True,
            }
            headers = {'Authorization': 'Basic ' +
                       base64.b64encode('trustee:' + new_peer.passphrase),
                       'Content-Type': 'application/json',
                       }
            data = json.dumps(params)
            try:
                response = urlfetch.fetch(url=new_peer.baseuri +
                                          '/trust/' +
                                          Config.actors[shorttype]['relationship'] +
                                          '/' + self.id,
                                          method=urlfetch.PUT,
                                          payload=data,
                                          headers=headers,
                                          )
                self.last_response_code = response.status_code
                self.last_response_message = response.content
            except:
                self.last_response_code = 408
                self.last_response_message = 'Not able to approve peer actor trust remotely'
            if response.status_code < 200 or response.status_code > 299:
                logging.debug('Not able to delete peer actor remotely')
        return new_peer

    def getTrustRelationship(self, peerid=None):
        if not peerid:
            return None
        return db.Trust.query(db.Trust.id == self.id,
                              db.Trust.peerid == peerid).get(use_cache=False)

    def getTrustRelationshipByType(self, type=None):
        if not type:
            return None
        return db.Trust.query(db.Trust.id == self.id,
                              db.Trust.type == type).fetch(use_cache=False)

    def getTrustRelationships(self, relationship='', peerid='', type=''):
        """Retrieves all trust relationships or filtered."""
        if len(relationship) > 0 and len(peerid) > 0 and len(type) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id,
                db.Trust.relationship == relationship,
                db.Trust.peerid == peerid,
                db.Trust.type == type).fetch(use_cache=False)
        elif len(peerid) > 0 and len(type) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id,
                db.Trust.peerid == peerid,
                db.Trust.type == type).fetch(use_cache=False)
        elif len(relationship) > 0 and len(peerid) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id,
                db.Trust.relationship == relationship,
                db.Trust.peerid == peerid).fetch(use_cache=False)
        elif len(relationship) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id,
                db.Trust.relationship == relationship).fetch(use_cache=False)
        elif len(peerid) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id,
                db.Trust.peerid == peerid).fetch(use_cache=False)
        elif len(type) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id,
                db.Trust.type == type).fetch(use_cache=False)
        else:
            relationships = db.Trust.query(db.Trust.id == self.id).fetch(use_cache=False)
        rels = []
        for rel in relationships:
            rels.append(trust.trust(self.id, rel.peerid))
        return rels

    def modifyTrustAndNotify(self, relationship=None, peerid=None, baseuri='', secret='', desc='', approved=None, verified=None, verificationToken=None, peer_approved=None):
        """Changes a trust relationship and noties the peer if approval is changed."""
        if not relationship or not peerid:
            return False
        relationships = self.getTrustRelationships(
            relationship=relationship, peerid=peerid)
        if not relationships:
            return False
        trust = relationships[0]
        # If we change approval status, send the changed status to our peer
        if approved is True and trust.approved is False:
            params = {
                'approved': True,
            }
            requrl = trust.baseuri + '/trust/' + relationship + '/' + self.id
            if trust.secret:
                headers = {'Authorization': 'Bearer ' + trust.secret,
                           'Content-Type': 'application/json',
                           }
            data = json.dumps(params)
            # Note the POST here instead of PUT. POST is used to used to notify about
            # state change in the relationship (i.e. not change the object as PUT
            # would do)
            logging.debug(
                'Trust relationship has been approved, notifying peer at url(' + requrl + ')')
            try:
                response = urlfetch.fetch(url=requrl,
                                          method=urlfetch.POST,
                                          payload=data,
                                          headers=headers
                                          )
                self.last_response_code = response.status_code
                self.last_response_message = response.content
            except:
                logging.debug('Not able to notify peer at url(' + requrl + ')')
                self.last_response_code = 500

        return relationships[0].modify(baseuri=baseuri,
                                       secret=secret,
                                       desc=desc,
                                       approved=approved,
                                       verified=verified,
                                       verificationToken=verificationToken,
                                       peer_approved=peer_approved)

    def createReciprocalTrust(self, url, secret=None, desc='', relationship='', type=''):
        """Creates a new reciprocal trust relationship locally and by requesting a relationship from a peer actor."""
        if len(url) == 0:
            return False
        if not secret or len(secret) == 0:
            return False
        Config = config.config()
        res = getPeerInfo(url)
        if not res or res["last_response_code"] < 200 or res["last_response_code"] >= 300:
            return False
        peer = res["data"]
        if not peer["id"] or not peer["type"] or len(peer["type"]) == 0:
            logging.info(
                "Received invalid peer info when trying to establish trust: " + url)
            return False
        if len(type) > 0:
            if type.lower() != peer["type"].lower():
                logging.info(
                    "Peer is of the wrong actingweb type: " + peer["type"])
                return False
        if not relationship or len(relationship) == 0:
            relationship = Config.default_relationship
        # Create trust, so that peer can do a verify on the relationship (using
        # verificationToken) when we request the relationship
        new_trust = trust.trust(self.id, peer["id"])
        if new_trust.trust:
            logging.warn("Trying to establish a new Reciprocal trust when peer relationship already exists (" + peer["id"] + ")")
            return False
        # Since we are initiating the relationship, we implicitly approve it
        # It is not verified until the peer has verified us
        new_trust.create(baseuri=url, secret=secret, type=peer["type"],
                         relationship=relationship, approved=True,
                         verified=False, desc=desc)
        # Add a sleep here to make sure that appengine has time to write the new
        # relationship to datastore before we try to create the new trust with peer
        # time.sleep(0.4)
        params = {
            'baseuri': Config.root + self.id,
            'id': self.id,
            'type': Config.type,
            'secret': secret,
            'desc': desc,
            'verify': new_trust.verificationToken,
        }
        requrl = url + '/trust/' + relationship
        data = json.dumps(params)
        logging.debug('Creating reciprocal trust at url(' +
                      requrl + ') and body (' + str(data) + ')')
        try:
            response = urlfetch.fetch(url=requrl,
                                      method=urlfetch.POST,
                                      payload=data,
                                      headers={
                                          'Content-Type': 'application/json', }
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            logging.debug(
                "Not able to create trust with peer, deleting my trust.")
            new_trust.delete()
            return False

        if self.last_response_code == 201 or self.last_response_code == 202:
            # Reload the trust to check if approval was done
            mod_trust = trust.trust(self.id, peer["id"])
            if not mod_trust.trust:
                logging.error(
                    "Couldn't find trust relationship after peer POST and verification")
                return False
            if self.last_response_code == 201:
                # Already approved by peer (probably auto-approved)
                # Do it direct on the trust (and not self.modifyTrustAndNotify) to avoid a callback
                # to the peer
                mod_trust.modify(peer_approved=True)
            return mod_trust
        else:
            logging.debug(
                "Not able to create trust with peer, deleting my trust.")
            new_trust.delete()
            return False

    def createVerifiedTrust(self, baseuri='', peerid=None, approved=False, secret=None, verificationToken=None, type=None, peer_approved=None, relationship=None, desc=''):
        """Creates a new trust when requested and call backs to initiating actor to verify relationship."""
        if not peerid or len(baseuri) == 0 or not relationship:
            return False
        requrl = baseuri + '/trust/' + relationship + '/' + self.id
        headers = {}
        if not secret or len(secret) == 0:
            logging.debug('No secret received from requesting peer(' + peerid +
                          ') at url (' + requrl + '). Verification is not possible.')
            verified = False
        else:
            headers = {'Authorization': 'Bearer ' + secret,
                       }
            logging.debug('Verifying trust at requesting peer(' + peerid +
                          ') at url (' + requrl + ') and secret(' + secret + ')')
            try:
                response = urlfetch.fetch(url=requrl,
                                          method=urlfetch.GET,
                                          headers=headers)
                self.last_response_code = response.status_code
                self.last_response_message = response.content
                try:
                    logging.debug(
                        'Verifying trust response JSON:' + response.content)
                    data = json.loads(response.content)
                    if data["verificationToken"] == verificationToken:
                        verified = True
                    else:
                        verified = False
                except ValueError:
                    logging.debug(
                        'No json body in response when verifying trust at url(' + requrl + ')')
                    verified = False
            except:
                logging.debug(
                    'No response when verifying trust at url' + requrl + ')')
                verified = False
        new_trust = trust.trust(self.id, peerid)
        if not new_trust.create(baseuri=baseuri, secret=secret, type=type, approved=approved, peer_approved=peer_approved,
                                relationship=relationship, verified=verified, desc=desc):
            return False
        else:
            return new_trust

    def deleteReciprocalTrust(self, peerid=None, deletePeer=False):
        """Deletes a trust relationship and requests deletion of peer's relationship as well."""
        failedOnce = False  # For multiple relationships, this will be True if at least one deletion at peer failed
        successOnce = False  # True if at least one relationship was deleted at peer
        if not peerid:
            rels = self.getTrustRelationships()
        else:
            rels = self.getTrustRelationships(peerid=peerid)
        for rel in rels:
            if deletePeer:
                url = rel.baseuri + '/trust/' + rel.relationship + '/' + self.id
                headers = {}
                if rel.secret:
                    headers = {'Authorization': 'Bearer ' + rel.secret,
                               }
                logging.debug(
                    'Deleting reciprocal relationship at url(' + url + ')')
                try:
                    response = urlfetch.fetch(url=url,
                                              method=urlfetch.DELETE,
                                              headers=headers)
                except:
                    logging.debug(
                        'Failed to delete reciprocal relationship at url(' + url + ')')
                    failedOnce = True
                    continue
                if (response.status_code < 200 or response.status_code > 299) and response.status_code != 404:
                    logging.debug(
                        'Failed to delete reciprocal relationship at url(' + url + ')')
                    failedOnce = True
                    continue
                else:
                    successOnce = True
            rel.trust.key.delete(use_cache=False)
        if deletePeer and (not successOnce or failedOnce):
            return False
        return True

    def createSubscription(self, peerid=None, target=None, subtarget=None, resource=None, granularity=None, subid=None, callback=False):
        new_sub = subscription.subscription(
            actor=self, peerid=peerid, subid=subid, callback=callback)
        new_sub.create(target=target, subtarget=subtarget, resource=resource,
                       granularity=granularity)
        return new_sub

    def createRemoteSubscription(self, peerid=None, target=None, subtarget=None, resource=None, granularity=None):
        """Creates a new subscription at peerid."""
        if not peerid or not target:
            return False
        Config = config.config()
        relationships = self.getTrustRelationships(peerid=peerid)
        if not relationships:
            return False
        peer = relationships[0]
        params = {
            'id': self.id,
            'target': target,
        }
        if subtarget:
            params['subtarget'] = subtarget
        if resource:
            params['resource'] = resource
        if granularity and len(granularity) > 0:
            params['granularity'] = granularity
        requrl = peer.baseuri + '/subscriptions/' + self.id
        data = json.dumps(params)
        headers = {'Authorization': 'Bearer ' + peer.secret,
                   'Content-Type': 'application/json',
                   }
        try:
            logging.debug('Creating remote subscription at url(' +
                          requrl + ') with body (' + str(data) + ')')
            response = urlfetch.fetch(url=requrl,
                                      method=urlfetch.POST,
                                      payload=data,
                                      headers=headers
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            return None
        try:
            logging.debug('Created remote subscription at url(' + requrl +
                          ') and got JSON response (' + response.content + ')')
            data = json.loads(response.content)
        except ValueError:
            return None
        if 'subscriptionid' in data:
            subid = data["subscriptionid"]
        else:
            return None
        if self.last_response_code == 201:
            self.createSubscription(peerid=peerid, target=target,
                                    subtarget=subtarget, resource=resource, granularity=granularity, subid=subid, callback=True)
            return response.headers['Location']
        else:
            return None

    def getSubscriptions(self, peerid=None, target=None, subtarget=None, resource=None, callback=False):
        """Retrieves subscriptions from db."""
        if not self.id:
            return None
        if peerid and target and subtarget and resource:
            subs = db.Subscription.query(
                db.Subscription.id == self.id,
                db.Subscription.peerid == peerid,
                db.Subscription.target == target,
                db.Subscription.subtarget == subtarget,
                db.Subscription.resource == resource).fetch(use_cache=False)
        elif peerid and target and subtarget:
            subs = db.Subscription.query(
                db.Subscription.id == self.id,
                db.Subscription.peerid == peerid,
                db.Subscription.target == target,
                db.Subscription.subtarget == subtarget).fetch(use_cache=False)
        elif peerid and target:
            subs = db.Subscription.query(
                db.Subscription.id == self.id,
                db.Subscription.peerid == peerid,
                db.Subscription.target == target).fetch(use_cache=False)
        elif peerid:
            subs = db.Subscription.query(
                db.Subscription.id == self.id,
                db.Subscription.peerid == peerid).fetch(use_cache=False)
        elif target and subtarget and resource:
            subs = db.Subscription.query(
                db.Subscription.id == self.id,
                db.Subscription.target == target,
                db.Subscription.subtarget == subtarget,
                db.Subscription.resource == resource).fetch(use_cache=False)
        elif target and subtarget:
            subs = db.Subscription.query(
                db.Subscription.id == self.id,
                db.Subscription.target == target,
                db.Subscription.subtarget == subtarget).fetch(use_cache=False)
        elif target:
            subs = db.Subscription.query(
                db.Subscription.id == self.id,
                db.Subscription.target == target).fetch(use_cache=False)
        else:
            subs = db.Subscription.query(
                db.Subscription.id == self.id).fetch(use_cache=False)
        # For some reason, doing a querit where callback is included results in a
        # perfect match (everthing returned), so we need to apply callback as a
        # filter
        ret = []
        for sub in subs:
            if sub.callback == callback:
                ret.append(sub)
        return ret

    def getSubscription(self, peerid=None, subid=None, callback=False):
        """Retrieves a single subscription identified by peerid and subid."""
        if not subid:
            return False
        sub = subscription.subscription(
            actor=self, peerid=peerid, subid=subid, callback=callback)
        if sub.subscription:
            return sub

    def deleteRemoteSubscription(self, peerid=None, subid=None):
        if not subid or not peerid:
            return False
        trust = self.getTrustRelationship(peerid=peerid)
        if not trust:
            return False
        sub = self.getSubscription(peerid=peerid, subid=subid)
        if not sub:
            sub = self.getSubscription(peerid=peerid, subid=subid, callback=True)
        if not sub.callback:
            url = trust.baseuri + '/subscriptions/' + self.id + '/' + subid
        else:
            url = trust.baseuri + '/callbacks/subscriptions/' + self.id + '/' + subid
        headers = {'Authorization': 'Bearer ' + trust.secret,
                   }
        try:
            logging.debug('Deleting remote subscription at url(' + url + ')')
            response = urlfetch.fetch(url=url,
                                      method=urlfetch.DELETE,
                                      headers=headers)
            self.last_response_code = response.status_code
            self.last_response_message = response.content
            if response.status_code == 204:
                return True
            else:
                logging.debug(
                    'Failed to delete remote subscription at url(' + url + ')')
                return False
        except:
            return False

    def deleteSubscription(self, peerid=None, subid=None, callback=False):
        """Deletes a specified subscription"""
        if not subid:
            return False
        sub = subscription.subscription(
            self, peerid=peerid, subid=subid, callback=callback)
        return sub.delete()

    def callbackSubscription(self, peerid=None, sub=None, diff=None, blob=None):
        if not peerid or not diff or not sub or not blob:
            logging.warn("Missing parameters in callbackSubscription")
            return
        if sub.granularity == "none":
            return
        trust = self.getTrustRelationship(peerid)
        if not trust:
            return
        params = {
            'id': self.id,
            'subscriptionid': sub.subid,
            'target': sub.target,
            'sequence': diff.seqnr,
            'timestamp': str(diff.timestamp),
            'granularity': sub.granularity,
        }
        if sub.subtarget:
            params['subtarget'] = sub.subtarget
        if sub.resource:
            params['resource'] = sub.resource
        if sub.granularity == "high":
            try:
                params['data'] = json.loads(blob)
            except:
                params['data'] = blob
        if sub.granularity == "low":
            Config = config.config()
            params['url'] = Config.root + self.id + '/subscriptions/' + \
                trust.peerid + '/' + sub.subid + '/' + str(diff.seqnr)
        requrl = trust.baseuri + '/callbacks/subscriptions/' + self.id + '/' + sub.subid
        data = json.dumps(params)
        headers = {'Authorization': 'Bearer ' + trust.secret,
                   'Content-Type': 'application/json',
                   }
        try:
            logging.debug('Doing a callback on subscription at url(' +
                          requrl + ') with body(' + str(data) + ')')
            response = urlfetch.fetch(url=requrl,
                                      method=urlfetch.POST,
                                      payload=data.encode('utf-8'),
                                      headers=headers
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
            if response.status_code == 204 and sub.granularity == "high":
                sub.clearDiff(diff.seqnr)
        except:
            logging.debug(
                'Peer did not respond to callback on url(' + requrl + ')')
            self.last_response_code = 0
            self.last_response_message = 'No response from peer for subscription callback'

    def registerDiffs(self, target=None, subtarget=None, resource=None, blob=None):
        """Registers a blob diff against all subscriptions with the correct target, subtarget, and resource."""
        if blob is None or not target:
            return
        # Get all subscriptions, both with the specific subtarget/resource and those
        # without
        subs = self.getSubscriptions(
            target=target, subtarget=None, resource=None, callback=False)
        if subtarget and resource:
            logging.debug("registerDiffs() - blob(" + blob + "), target(" +
                          target + "), subtarget(" + subtarget + "), resource(" +
                          resource + "), # of subs(" + str(len(subs)) + ")")
        elif subtarget:
            logging.debug("registerDiffs() - blob(" + blob + "), target(" +
                          target + "), subtarget(" + subtarget + 
                          "), # of subs(" + str(len(subs)) + ")")            
        else:
            logging.debug("registerDiffs() - blob(" + blob + "), target(" +
                          target + "), # of subs(" + str(len(subs)) + ")")
        for sub in subs:
            # Skip the ones without correct subtarget
            if subtarget and sub.subtarget and sub.subtarget != subtarget:
                logging.debug("     - no match on subtarget, skipping...")
                continue
            # Skip the ones without correct resource
            if resource and sub.resource and sub.resource != resource:
                logging.debug("     - no match on resource, skipping...")
                continue
            subObj = subscription.subscription(
                self, peerid=sub.peerid, subid=sub.subid)
            logging.debug("     - processing subscription(" + sub.subid +
                          ") for peer(" + sub.peerid + ") with target(" + 
                          subObj.target + ") subtarget(" + str(subObj.subtarget or '') +
                          ") and resource(" + str(subObj.resource or '') + ")")
            finblob = None
            # Subscription with a resource, but this diff is on a higher level
            if (not resource or not subtarget) and subObj.subtarget and subObj.resource:
                # Create a json diff on the subpart that this subscription
                # covers
                try:
                    jsonblob = json.loads(blob)
                    if not subtarget:
                        subblob = json.dumps(jsonblob[subObj.subtarget][subObj.resource])
                    else:
                        subblob = json.dumps(jsonblob[subObj.resource])
                except:
                    # The diff does not contain the resource
                    subblob = None
                    logging.debug("         - subscription has resource(" +
                                  subObj.resource + "), no matching blob found in diff")
                    continue
                logging.debug("         - subscription has resource(" +
                              subObj.resource + "), adding diff(" + subblob + ")")
                finblob = subblob
            # The diff is on the resource, but the subscription is on a 
            # higher level
            elif resource and not subObj.resource:
                # Create a data["subtarget"]["resource"] = blob diff to give correct level
                # of diff to subscriber
                upblob = {}
                try:
                    jsonblob = json.loads(blob)
                    upblob[subtarget][resource] = jsonblob
                except:
                    upblob[subtarget][resource] = blob
                finblob = json.dumps(upblob)
                logging.debug("         - diff has resource(" + resource +
                              "), subscription has not, adding diff(" + finblob + ")")
            # Subscriptions with subtarget, but this diff is on a higher level
            elif not subtarget and subObj.subtarget:
                # Create a json diff on the subpart that this subscription
                # covers
                try:
                    jsonblob = json.loads(blob)
                    subblob = json.dumps(jsonblob[subObj.subtarget])
                except:
                    # The diff blob does not contain the subtarget
                    subblob = None
                    continue
                logging.debug("         - subscription has subtarget(" +
                              subObj.subtarget + "), adding diff(" + subblob + ")")
                finblob = subblob
            # The diff is on the subtarget, but the subscription is on the
            # higher level
            elif subtarget and not subObj.subtarget:
                # Create a data["subtarget"] = blob diff to give correct level
                # of diff to subscriber
                upblob = {}
                try:
                    jsonblob = json.loads(blob)
                    upblob[subtarget] = jsonblob
                except:
                    upblob[subtarget] = blob
                finblob = json.dumps(upblob)
                logging.debug("         - diff has subtarget(" + subtarget +
                              "), subscription has not, adding diff(" + finblob + ")")
            else:
                # The diff is correct for the subscription
                logging.debug(
                              "         - exact target/subtarget match, adding diff(" + blob + ")")
                finblob = blob
            diff = subObj.addDiff(blob=finblob)
            if not diff:
                logging.warn("Failed when registering a diff to subscription (" +
                             sub.subid + "). Will not send callback.")
            else:
                deferred.defer(self.callbackSubscription, peerid=sub.peerid,
                               sub=subObj, diff=diff, blob=finblob)

    def __init__(self, id=''):
        self.get(id)
