#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import auth
from actingweb import config

import webapp2
from on_aw import on_aw_delete
import json


class MainPage(webapp2.RequestHandler):

    def get(self, id):
        if self.request.get('_method') == 'DELETE':
            self.delete(id)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='', subpath='')
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='/', method='GET'):
            self.response.set_status(403)
            return
        pair = {
            'id': myself.id,
            'creator': myself.creator,
            'passphrase': myself.passphrase,
        }
        trustee_root = myself.getProperty('trustee_root').value
        if trustee_root and len(trustee_root) > 0:
            pair['trustee_root'] = trustee_root
        out = json.dumps(pair)
        self.response.write(out.encode('utf-8'))
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200)

    def delete(self, id):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='', subpath='')
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='/', method='DELETE'):
            self.response.set_status(403)
            return
        on_aw_delete.on_aw_delete_actor(myself=myself, req=self, auth=check)
        myself.delete()
        self.response.set_status(204)
        return

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id><:/?>', MainPage, name='MainPage'),
], debug=True)
