#!/usr/bin/env python
#
from actingweb import actor
from actingweb import config

import webapp2

import os
from google.appengine.ext.webapp import template
import json


class MainPage(webapp2.RequestHandler):

    def get(self):
        if self.request.get('_method') == 'POST':
            self.post()
            return
        Config = config.config()
        if Config.ui:
            template_values = {
            }
            path = os.path.join(os.path.dirname(__file__), 'templates/aw-root-factory.html')
            self.response.write(template.render(path, template_values).encode('utf-8'))
        else:
            self.response.set_status(404)

    def post(self):
        myself = actor.actor()
        Config = config.config()
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            is_json = True
            if 'creator' in params:
                creator = params['creator']
            else:
                creator = ''
            if 'trustee_root' in params:
                trustee_root = params['trustee_root']
            else:
                trustee_root = ''
            if 'passphrase' in params:
                passphrase = params['passphrase']
            else:
                passphrase = ''
        except ValueError:
            is_json = False
            creator = self.request.get('creator')
            trustee_root = self.request.get('trustee_root')
            passphrase = self.request.get('passphrase')
        myself.create(url=self.request.url, creator=creator,
                      passphrase=passphrase)
        if len(trustee_root) > 0:
            myself.setProperty('trustee_root', trustee_root)
        self.response.headers.add_header("Location", Config.root + myself.id)
        if Config.www_auth == 'oauth' and not is_json:
            self.redirect(Config.root + myself.id + '/www')
            return
        pair = {
            'id': myself.id,
            'creator': myself.creator,
            'passphrase': myself.passphrase,
        }
        if len(trustee_root) > 0:
            pair['trustee_root'] = trustee_root
        if Config.ui and not is_json:
            path = os.path.join(os.path.dirname(__file__), 'templates/aw-root-created.html')
            self.response.write(template.render(path, pair).encode('utf-8'))
            return
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')

application = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
