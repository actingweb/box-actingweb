#!/usr/bin/env python
#
from actingweb import actor
from actingweb import config
from actingweb import trust
from actingweb import auth

import webapp2

import os
from google.appengine.ext.webapp import template
import json
import logging
import datetime
import time


# /trust handlers
#
# GET /trust with query parameters (relationship, type, and peerid) to retrieve trust relationships (auth: only creator and admins allowed)
# POST /trust with json body to initiate a trust relationship between this
#   actor and another (reciprocal relationship) (auth: only creator and admins allowed)
# POST /trust/{relationship} with json body to create new trust
#   relationship (see config.py for default relationship and auto-accept, no
#   auth required)
# GET /trust/{relationship}}/{actorid} to get details on a specific relationship (auth: creator, admin, or peer secret)
# POST /trust/{relationship}}/{actorid} to send information to a peer about changes in the relationship
# PUT /trust/{relationship}}/{actorid} with a json body to change details on a relationship (baseuri, secret, desc) (auth: creator,
#   admin, or peer secret)
# DELETE /trust/{relationship}}/{actorid} to delete a relationship (with
#   ?peer=true if the delete is from the peer) (auth: creator, admin, or
#   peer secret)

# Handling requests to trust/
class rootHandler(webapp2.RequestHandler):

    def get(self, id):
        if self.request.get('_method') == 'POST':
            self.post(id)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='trust')
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='trust', method='GET'):
            self.response.set_status(403)
            return
        relationship = ''
        type = ''
        peerid = ''
        relationship = self.request.get('relationship')
        type = self.request.get('type')
        peerid = self.request.get('peerid')

        relationships = myself.getTrustRelationships(
            relationship=relationship, peerid=peerid, type=type)
        if not relationships:
            self.response.set_status(404, 'Not found')
            return
        pairs = []
        for rel in relationships:
            pairs.append({
                'baseuri': rel.baseuri,
                'id': myself.id,
                'peerid': rel.peerid,
                'relationship': rel.relationship,
                'approved': rel.approved,
                'peer_approved': rel.peer_approved,
                'verified': rel.verified,
                'type': rel.type,
                'desc': rel.desc,
                'secret': rel.secret,
            })
        out = json.dumps(pairs)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200, 'Ok')

    def post(self, id):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='trust')
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='trust', method='POST'):
            self.response.set_status(403)
            return
        secret = ''
        desc = ''
        relationship = Config.default_relationship
        type = ''
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'url' in params:
                url = params['url']
            else:
                url = ''
            if 'relationship' in params:
                relationship = params['relationship']
            if 'type' in params:
                type = params['type']
            if 'desc' in params:
                desc = params['desc']
        except ValueError:
            url = self.request.get('url')
            relationship = self.request.get('relationship')
            type = self.request.get('type')
        if len(url) == 0:
            self.response.set_status(400, 'Missing peer URL')
            return
        secret = Config.newToken()

        new_trust = myself.createReciprocalTrust(
            url=url, secret=secret, desc=desc, relationship=relationship, type=type)
        if not new_trust:
            self.response.set_status(408, 'Unable to create trust relationship')
            return
        self.response.headers.add_header(
            "Location", str(Config.root + myself.id + '/trust/' + new_trust.relationship + '/' + new_trust.peerid))
        pair = {
            'baseuri': new_trust.baseuri,
            'id': myself.id,
            'peerid': new_trust.peerid,
            'relationship': new_trust.relationship,
            'approved': new_trust.approved,
            'peer_approved': new_trust.peer_approved,
            'verified': new_trust.verified,
            'type': new_trust.type,
            'desc': new_trust.desc,
            'secret': new_trust.secret,
        }
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')


# Handling requests to /trust/*, e.g. /trust/friend
class relationshipHandler(webapp2.RequestHandler):

    def get(self, id, relationship):
        if self.request.get('_method') == 'POST':
            self.post(id, relationship)
            return
        self.response.set_status(404, "Not found")

    def post(self, id, relationship):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='trust', subpath=relationship, add_response=False)
        if not myself:
            return
        if not check.checkAuthorisation(path='trust', subpath='<type>', method='POST'):
            self.response.set_status(403)
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'baseuri' in params:
                baseuri = params['baseuri']
            else:
                baseuri = ''
            if 'id' in params:
                peerid = params['id']
            else:
                peerid = ''
            if 'type' in params:
                type = params['type']
            else:
                type = ''
            if 'secret' in params:
                secret = params['secret']
            else:
                secret = ''
            if 'desc' in params:
                desc = params['desc']
            else:
                desc = ''
            if 'verify' in params:
                verificationToken = params['verify']
            else:
                verificationToken = None
        except ValueError:
            self.response.set_status(400, 'No json content')
            return

        if len(baseuri) == 0 or len(peerid) == 0 or len(type) == 0:
            self.response.set_status(400, 'Missing mandatory attributes')
            return
        if Config.auto_accept_default_relationship and Config.default_relationship == relationship:
            approved = True
        else:
            approved = False
        # Since we received a request for a relationship, assume that peer has approved
        new_trust = myself.createVerifiedTrust(baseuri=baseuri, peerid=peerid, approved=approved, secret=secret,
                                               verificationToken=verificationToken, type=type, peer_approved=True, relationship=relationship, desc=desc)
        if not new_trust:
            self.response.set_status(403, 'Forbidden')
            return
        self.response.headers.add_header(
            "Location", str(Config.root + myself.id + '/trust/' + new_trust.relationship + "/" + new_trust.peerid))
        pair = {
            'baseuri': new_trust.baseuri,
            'id': myself.id,
            'peerid': new_trust.peerid,
            'relationship': new_trust.relationship,
            'approved': new_trust.approved,
            'peer_approved': new_trust.peer_approved,
            'verified': new_trust.verified,
            'type': new_trust.type,
            'desc': new_trust.desc,
            'secret': new_trust.secret,
        }
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        if approved:
            self.response.set_status(201, 'Created')
        else:
            self.response.set_status(202, 'Accepted')


# Handling requests to specific relationships, e.g. /trust/friend/12f2ae53bd
class trustHandler(webapp2.RequestHandler):

    def get(self, id, relationship, peerid):
        if self.request.get('_method') == 'PUT':
            self.put(id, relationship, peerid)
            return
        if self.request.get('_method') == 'DELETE':
            self.delete(id, relationship, peerid)
            return
        logging.debug('GET trust headers: ' + str(self.request.headers))
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='trust', subpath=relationship)
        if not myself or check.response["code"] != 200:
            logging.debug('Failed authentication.')
            return
        if not check.checkAuthorisation(path='trust', subpath='<type>/<id>', method='GET', peerid=peerid):
            self.response.set_status(403)
            return
        relationships = myself.getTrustRelationships(
            relationship=relationship, peerid=peerid)
        if not relationships:
            self.response.set_status(404, 'Not found')
            return
        my_trust = relationships[0]
        # If the peer did a GET to verify
        if check.trust and check.trust.peerid == peerid and not my_trust.verified:
            my_trust.modify(verified=True)
            verificationToken = my_trust.verificationToken
        else:
            verificationToken = ''
        pair = {
            'baseuri': my_trust.baseuri,
            'id': myself.id,
            'peerid': my_trust.peerid,
            'relationship': my_trust.relationship,
            'approved': my_trust.approved,
            'peer_approved': my_trust.peer_approved,
            'verified': my_trust.verified,
            'verificationToken': verificationToken,
            'type': my_trust.type,
            'desc': my_trust.desc,
            'secret': my_trust.secret,
        }
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        if my_trust.approved:
            self.response.set_status(200, 'Ok')
        else:
            self.response.set_status(202, 'Accepted')

    def post(self, id, relationship, peerid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='trust', subpath=relationship)
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='trust', subpath='<type>/<id>', method='POST', peerid=peerid):
            self.response.set_status(403)
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            peer_approved = None
            if 'approved' in params:
                if params['approved'] and params['approved'] == True:
                    peer_approved = True
        except ValueError:
            self.response.set_status(400, 'No json content')
            return
        if myself.modifyTrustAndNotify(relationship=relationship, peerid=peerid, peer_approved=peer_approved):
            self.response.set_status(204, 'Ok')
        else:
            self.response.set_status(405, 'Not modified')

    def put(self, id, relationship, peerid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='trust', subpath=relationship)
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='trust', subpath='<type>/<id>', method='PUT', peerid=peerid):
            self.response.set_status(403)
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'baseuri' in params:
                baseuri = params['baseuri']
            else:
                baseuri = ''
            if 'desc' in params:
                desc = params['desc']
            else:
                desc = ''
            if 'approved' in params:
                if params['approved'] == True or params['approved'].lower() == "true":
                    approved = True
            else:
                approved = None
        except ValueError:
            if not self.request.get('_method') or self.request.get('_method') != "PUT":
                self.response.set_status(400, 'No json content')
                return
            if self.request.get('approved') and len(self.request.get('approved')) > 0:
                if self.request.get('approved').lower() == "true":
                    approved = True
                else:
                    approved = None
            if self.request.get('baseuri') and len(self.request.get('baseuri')) > 0:
                baseuri = self.request.get('baseuri')
            else:
                baseuri = ''
            if self.request.get('desc') and len(self.request.get('desc')) > 0:
                desc = self.request.get('desc')
            else:
                desc = ''
        if myself.modifyTrustAndNotify(relationship=relationship, peerid=peerid, baseuri=baseuri, approved=approved, desc=desc):
            self.response.set_status(204, 'Ok')
        else:
            self.response.set_status(405, 'Not modified')

    def delete(self, id, relationship, peerid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='trust', subpath=relationship, add_response=False)
        if not myself or (check.response["code"] != 200 and check.response["code"] != 401):
            auth.add_auth_response(appreq=self, auth_obj=check)
            return
        # We allow non-approved peers to delete even if we haven't approved the relationship yet
        if not check.checkAuthorisation(path='trust', subpath='<type>/<id>', method='DELETE', peerid=peerid, approved=False):
            self.response.set_status(403)
            return
        isPeer = False
        if check.trust and check.trust.peerid == peerid:
            isPeer = True
        else:
            # Use of GET param peer=true is a way of forcing no deletion of a peer
            # relationship even when requestor is not a peer (primarily for testing purposes)
            peerGet = self.request.get('peer').lower()
            if peerGet.lower() == "true":
                isPeer = True
        Config = config.config()
        relationships = myself.getTrustRelationships(
            relationship=relationship, peerid=peerid)
        if not relationships:
            self.response.set_status(404, 'Not found')
            return
        my_trust = relationships[0]
        if isPeer:
            deleted = myself.deleteReciprocalTrust(peerid=peerid, deletePeer=False)
        else:
            deleted = myself.deleteReciprocalTrust(peerid=peerid, deletePeer=True)
        if not deleted:
            self.response.set_status(502, 'Not able to delete relationship with peer.')
            return
        self.response.set_status(204, 'Ok')


application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/trust<:/?>', rootHandler, name='rootHandler'),
    webapp2.Route(r'/<id>/trust/<relationship><:/?>',
                  relationshipHandler, name='relationshipHandler'),
    webapp2.Route(r'/<id>/trust/<relationship>/<peerid><:/?>', trustHandler, name='trustHandler'),
], debug=True)
