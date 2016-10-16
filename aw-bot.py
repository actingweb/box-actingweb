#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
import logging
import json
from actingweb import actor
from actingweb import auth
from actingweb import config
from on_aw import on_aw_bot
import webapp2


class MainPage(webapp2.RequestHandler):

    def post(self, path):
        """Handles POST callbacks for bots."""

        Config = config.config()
        if not Config.bot['token'] or len(Config.bot['token']) == 0:
            self.response.set_status(404)
            return
        check = auth.auth(id=None)
        check.oauth.token = Config.bot['token']
        ret = on_aw_bot.on_bot_post(req=self, auth=check, path=path)
        if ret and ret >= 100 and ret < 999:
            self.response.set_status(ret)
            return
        elif ret:
            self.response.set_status(204)
            return
        else:
            self.response.set_status(404)
            return

application = webapp2.WSGIApplication([
    webapp2.Route(r'/bot<:/?><path:(.*)>', MainPage, name='MainPage'),
], debug=True)
