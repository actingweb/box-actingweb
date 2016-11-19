#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
import logging
import json
from actingweb import actor
from actingweb import auth
from actingweb import config
from actingweb import aw_proxy
import webapp2


class MainPage(webapp2.RequestHandler):

    def put(self, id, path):
        """Handles PUT for devtest"""

        Config = config.config()
        if not Config.devtest:
            self.response.set_status(404)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='devtest', subpath=path)
        if not myself or check.response["code"] != 200:
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
        except:
            params = None
        paths = path.split('/')
        if paths[0] == 'proxy':
            mytwin = myself.getPeerTrustee(shorttype='myself')
            if mytwin:
                if paths[1] == 'properties' and paths[2] and len(paths[2]) > 0:
                        proxy = aw_proxy.aw_proxy(peer_target=mytwin)
                        if params:
                            proxy.changeResource('/properties/' + paths[2], params = params)
                        self.response.set_status(proxy.last_response_code)
                        return
        elif paths[0] == 'ping':
            self.response.set_status(204)
            return
        self.response.set_status(404)

    def delete(self, id, path):
        """Handles DELETE for devtest"""

        Config = config.config()
        if not Config.devtest:
            self.response.set_status(404)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='devtest', 
                                                      subpath=path)
        if not myself or check.response["code"] != 200:
            return
        paths = path.split('/')
        if paths[0] == 'proxy':
            mytwin = myself.getPeerTrustee(shorttype='myself')
            if mytwin:
                if paths[1] == 'properties':
                    proxy = aw_proxy.aw_proxy(peer_target=mytwin)
                    prop = proxy.deleteResource(path='/properties')
                    self.response.set_status(proxy.last_response_code)
                    return
        elif paths[0] == 'ping':
            self.response.set_status(204)
            return
        self.response.set_status(404)

    def get(self, id, path):
        """Handles GET for devtest"""

        Config = config.config()
        if not Config.devtest:
            self.response.set_status(404)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='devtest', 
                                                      subpath=path)
        if not myself or check.response["code"] != 200:
            return
        paths = path.split('/')
        if paths[0] == 'proxy':
            mytwin = myself.getPeerTrustee(shorttype='myself')
            if mytwin:
                if paths[1] == 'properties':
                    proxy = aw_proxy.aw_proxy(peer_target=mytwin)
                    prop = proxy.getResource(path='/properties')
                    if proxy.last_response_code != 200:
                        self.response.set_status(proxy.last_response_code)
                        return
                    out = json.dumps(prop)
                    self.response.write(out.encode('utf-8'))
                    self.response.headers["Content-Type"] = "application/json"
                    self.response.set_status(200)
                    return
        elif paths[0] == 'ping':
            self.response.set_status(204)
            return
        self.response.set_status(404)

    def post(self, id, path):
        """Handles POST for devtest"""

        Config = config.config()
        if not Config.devtest:
            self.response.set_status(404)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='devtest', 
                                                      subpath=path)
        if not myself or check.response["code"] != 200:
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
        except:
            params = None
        paths = path.split('/')
        if paths[0] == 'proxy':
            mytwin = myself.getPeerTrustee(shorttype='myself')
            if mytwin:
                if paths[1] == 'create':
                        proxy = aw_proxy.aw_proxy(peer_target=mytwin)
                        meta = proxy.getResource(path='/meta')
                        if params:
                            proxy.createResource('/properties', params = params)
                        out = json.dumps(meta)
                        self.response.write(out.encode('utf-8'))
                        self.response.headers["Content-Type"] = "application/json"
                        self.response.headers["Location"] = mytwin.baseuri
                        self.response.set_status(200)
                        return
        elif paths[0] == 'ping':
            self.response.set_status(204)
            return
        self.response.set_status(404)

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/devtest<:/?><path:(.*)>', MainPage, name='MainPage'),
], debug=True)
