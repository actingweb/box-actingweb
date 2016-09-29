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


class rootHandler(webapp2.RequestHandler):
    """Handles requests to /subscription"""

    def get(self, id):
        if self.request.get('_method') == 'POST':
            self.post(id)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscriptions')
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='subscriptions', method='GET'):
            self.response.set_status(403)
            return
        peerid = self.request.get('peerid')
        target = self.request.get('target')
        subtarget = self.request.get('subtarget')

        subscriptions = myself.getSubscriptions(peerid=peerid, target=target, subtarget=subtarget)
        if not subscriptions:
            self.response.set_status(404, 'Not found')
            return
        pairs = []
        for sub in subscriptions:
            pairs.append({
                'peerid': sub.peerid,
                'subscriptionid': sub.subid,
                'target': sub.target,
                'subtarget': sub.subtarget,
                'granularity': sub.granularity,
                'sequence': sub.seqnr,
            })
        data = {'data': pairs,
                }
        out = json.dumps(data)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200, 'Ok')

    def post(self, id):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscriptions')
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='subscriptions', method='POST'):
            self.response.set_status(403)
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'peerid' in params:
                peerid = params['peerid']
            if 'target' in params:
                target = params['target']
            if 'subtarget' in params:
                subtarget = params['subtarget']
            else:
                subtarget = None
            if 'granularity' in params:
                granularity = params['granularity']
            else:
                granularity = 'none'
        except ValueError:
            peerid = self.request.get('peerid')
            target = self.request.get('target')
            subtarget = self.request.get('subtarget')
            granularity = self.request.get('granularity')
        if not peerid or len(peerid) == 0:
            self.response.set_status(400, 'Missing peer URL')
            return
        if not target or len(target) == 0:
            self.response.set_status(400, 'Missing target')
            return
        remoteLoc = myself.createRemoteSubscription(
            peerid=peerid, target=target, subtarget=subtarget, granularity=granularity)
        if not remoteLoc:
            self.response.set_status(408, 'Unable to create remote subscription with peer')
            return
        self.response.headers.add_header("Location", remoteLoc)
        self.response.set_status(204, 'Created')


# Handling requests to /subscription/*, e.g. /subscription/<peerid>
class relationshipHandler(webapp2.RequestHandler):

    def get(self, id, peerid):
        if self.request.get('_method') == 'POST':
            self.post(id, peerid)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscriptions')
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='subscriptions', method='GET', peerid=peerid):
            self.response.set_status(403)
            return
        target = self.request.get('target')
        subtarget = self.request.get('subtarget')

        subscriptions = myself.getSubscriptions(peerid=peerid, target=target, subtarget=subtarget)
        if not subscriptions:
            self.response.set_status(404, 'Not found')
            return
        pairs = []
        for sub in subscriptions:
            pairs.append({
                'subscriptionid': sub.subid,
                'target': sub.target,
                'subtarget': sub.subtarget,
                'granularity': sub.granularity,
                'sequence': sub.seqnr,
            })
        data = {'data': pairs,
                }
        out = json.dumps(data)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200, 'Ok')

    def post(self, id, peerid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscriptions')
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='subscriptions', method='POST', peerid=peerid):
            self.response.set_status(403)
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'target' in params:
                target = params['target']
            else:
                self.response.set_status(400, 'No target in request')
                return
            if 'subtarget' in params:
                subtarget = params['subtarget']
            else:
                subtarget = None
            if 'granularity' in params:
                granularity = params['granularity']
            else:
                granularity = 'none'
        except ValueError:
            self.response.set_status(400, 'No json body')
            return
        if peerid != check.acl["peerid"]:
            logging.warn("Peer " + peerid +
                         " tried to create a subscription for peer " + check.acl["peerid"])
            self.response.set_status(403, 'Forbidden. Wrong peer id in request')
            return
        # We need to validate that this peer has GET rights on what it wants to subscribe to
        if not check.checkAuthorisation(path=target, subpath=subtarget, method='GET', peerid=peerid):
            self.response.set_status(403)
            return
        new_sub = myself.createSubscription(
            peerid=check.acl["peerid"], target=target, subtarget=subtarget, granularity=granularity)
        if not new_sub:
            self.response.set_status(500, 'Unable to create new subscription')
            return
        self.response.headers.add_header(
            "Location", str(Config.root + myself.id + '/subscriptions/' + new_sub.peerid + '/' + new_sub.subid))
        pair = {
            'subscriptionid': new_sub.subid,
            'target': new_sub.target,
            'subtarget': new_sub.subtarget,
            'granularity': new_sub.granularity,
            'sequence': new_sub.seqnr,
        }
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')


class subscriptionHandler(webapp2.RequestHandler):
    """ Handling requests to specific subscriptions, e.g. /subscriptions/<peerid>/12f2ae53bd"""

    def get(self, id, peerid, subid):
        if self.request.get('_method') == 'PUT':
            self.put(id, peerid, subid)
            return
        if self.request.get('_method') == 'DELETE':
            self.delete(id, peerid, subid)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscriptions', subpath=peerid + '/' + subid)
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='subscriptions', subpath='<id>/<id>', method='GET', peerid=peerid):
            self.response.set_status(403)
            return
        sub = myself.getSubscription(peerid=peerid, subid=subid)
        if not sub:
            self.response.set_status(404, "Subscription does not exist")
            return
        diffs = sub.getDiffs()
        pairs = []
        for diff in diffs:
            try:
                d = json.loads(diff.diff)
            except:
                d = diff.diff
            pairs.append({
                'sequence': diff.seqnr,
                'timestamp': str(diff.timestamp),
                'data': d,
            })
        if len(pairs) == 0:
            self.response.set_status(404, 'No diffs available')
            return
        data = {'target': sub.target,
                'subtarget': sub.subtarget,
                'data': pairs,
                }
        out = json.dumps(data)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200, 'Ok')

    def put(self, id, peerid, subid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscriptions', subpath=peerid + '/' + subid)
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='subscriptions', subpath='<id>/<id>', method='GET', peerid=peerid):
            self.response.set_status(403)
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'sequence' in params:
                seq = params['sequence']
            else:
                self.response.set_status(405, "Error in json body and no GET parameters")
                return
        except:
            seq = self.request.get('sequence')
            if len(seq) == 0:
                self.response.set_status(405, "Error in json body and no GET parameters")
                return
        try:
            if not isinstance(seq, int):
                seqnr = int(seq)
            else:
                seqnr = seq
        except ValueError:
            self.response.set_status(405, "Sequence does not contain a number")
            return
        sub = myself.getSubscription(peerid=peerid, subid=subid)
        if not sub:
            self.response.set_status(404, "Subscription does not exist")
            return
        sub.clearDiffs(seqnr=seqnr)
        self.response.set_status(204)
        return

    def delete(self, id, peerid, subid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscriptions', subpath=peerid + '/' + subid)
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='subscriptions', subpath='<id>/<id>', method='GET', peerid=peerid):
            self.response.set_status(403)
            return
        if not myself.deleteSubscription(peerid=peerid, subid=subid):
            self.response.set_status(404)
            return
        self.response.set_status(204)
        return


class diffHandler(webapp2.RequestHandler):
    """ Handling requests to specific diffs for one subscription and clears it, e.g. /subscriptions/<peerid>/<subid>/112"""

    def get(self, id, peerid, subid, seqid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscriptions', subpath=peerid + '/' + subid + '/' + seqid)
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='subscriptions', subpath='<id>/<id>', method='GET', peerid=peerid):
            self.response.set_status(403)
            return
        sub = myself.getSubscription(peerid=peerid, subid=subid)
        if not sub:
            self.response.set_status(404, "Subscription does not exist")
            return
        if not isinstance(seqid, int):
            seqid = int(seqid)
        diff = sub.getDiff(seqid)
        if not diff:
            self.response.set_status(404, 'No diffs available')
            return
        try:
            d = json.loads(diff.diff)
        except:
            d = diff.diff
        pairs = {
            'timestamp': str(diff.timestamp),
            'target': sub.target,
            'subtarget': sub.subtarget,
            'data': d,
        }
        sub.clearDiff(seqid)
        out = json.dumps(pairs)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200, 'Ok')


application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/subscriptions<:/?>', rootHandler, name='rootHandler'),
    webapp2.Route(r'/<id>/subscriptions/<peerid><:/?>',
                  relationshipHandler, name='relationshipHandler'),
    webapp2.Route(r'/<id>/subscriptions/<peerid>/<subid><:/?>',
                  subscriptionHandler, name='subscriptionHandler'),
    webapp2.Route(r'/<id>/subscriptions/<peerid>/<subid>/<seqid><:/?>',
                  diffHandler, name='diffHandler'),
], debug=True)
