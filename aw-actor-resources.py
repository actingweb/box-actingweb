#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
import json
import logging
from actingweb import actor
from actingweb import auth
from on_aw import on_aw_resources

import webapp2


class MainPage(webapp2.RequestHandler):

    def get(self, id, name):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='resources', subpath=name)
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='resources', subpath=name, method='GET'):
            self.response.set_status(403)
            return
        pair = on_aw_resources.on_get_resources(myself=myself,
                                                req=self,
                                                auth=check,
                                                name=name,
                                                params=self.request.get_all())
        if pair and any(pair): 
            out = json.dumps(pair)
            self.response.write(out.encode('utf-8'))
            self.response.headers["Content-Type"] = "application/json"
            self.response.set_status(200)
        else:
            self.response.set_status(404)

    def delete(self, id, name):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='resources', subpath=name)
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='resources', subpath=name, method='DELETE'):
            self.response.set_status(403)
            return
        pair = on_aw_resources.on_delete_resources(myself=myself,
                                                req=self,
                                                auth=check,
                                                name=name,
                                                params=self.request.get_all())
        if pair:
            if pair >= 100 and pair <= 999:
                return
            if any(pair): 
                out = json.dumps(pair)
                self.response.write(out.encode('utf-8'))
                self.response.headers["Content-Type"] = "application/json"
                self.response.set_status(200)
        else:
            self.response.set_status(404)

    def post(self, id, name):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='resources', subpath=name)
        if not myself or check.response["code"] != 200:
            return
        if not check.checkAuthorisation(path='resources', subpath=name, method='POST'):
            self.response.set_status(403)
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
        except:
            self.response.set_status(405, "Error in json body")
            return
        pair = on_aw_resources.on_post_resources(myself=myself,
                                                 req=self,
                                                 auth=check,
                                                 name=name,
                                                 params=params)
        if pair:
            if pair >= 100 and pair <= 999:
                return
            if any(pair):
                out = json.dumps(pair)
                self.response.write(out.encode('utf-8'))
                self.response.headers["Content-Type"] = "application/json"
                self.response.set_status(201, 'Created')
        else:
            self.response.set_status(404)

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/resources<:/?><name:(.*)>', MainPage, name='MainPage'),
], debug=True)
