#!/usr/bin/env python
import webapp2
import os
import logging
import time
from actingweb import config


class MainPage(webapp2.RequestHandler):

    def get(self):
        if not self.request.get('code'):
            self.response.set_status(400, "Bad request. No code.")
            return
        code = self.request.get('code')
        id = self.request.get('state')
        Config = config.config()
        self.redirect(Config.root + str(id) + '/oauth?code=' + str(code))

application = webapp2.WSGIApplication([
    webapp2.Route(r'/oauth', MainPage, name='MainPage'),
], debug=True)
