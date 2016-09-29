#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import auth
from actingweb import config
from actingweb.db import db

import webapp2
import json

import os
from google.appengine.ext.webapp import template

# Load global configurations
Config = config.config()


class MainPage(webapp2.RequestHandler):

    def get(self, id, path):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='meta', subpath=path, add_response=False)
        # We accept no auth here, so don't check response code
        if not myself:
            return
        if not check.checkAuthorisation(path='meta', subpath=path, method='GET'):
            self.response.set_status(403)
            return

        if not path:
            values = {
                'id': id,
                'type': Config.type,
                'version': Config.version,
                'desc': Config.desc,
                'info': Config.info,
                'specification': Config.specification,
                'aw_version': Config.aw_version,
                'aw_supported': Config.aw_supported,
                'aw_formats': Config.aw_formats,
            }
            out = json.dumps(values)
            self.response.write(out.encode('utf-8'))
            self.response.headers["Content-Type"] = "application/json"
            return

        elif path == 'id':
            out = id
        elif path == 'type':
            out = Config.type
        elif path == 'version':
            out = Config.version
        elif path == 'desc':
            out = Config.desc + myself.id
        elif path == 'info':
            out = Config.info
        elif path == 'specification':
            out = Config.specification
        elif path == 'actingweb/version':
            out = Config.aw_version
        elif path == 'actingweb/supported':
            out = Config.aw_supported
        elif path == 'actingweb/formats':
            out = Config.aw_formats
        else:
            self.response.set_status(404)
            return
        self.response.write(out.encode('utf-8'))

application = webapp2.WSGIApplication([
    (r'/(.*)/meta/?(.*)', MainPage),
], debug=True)
