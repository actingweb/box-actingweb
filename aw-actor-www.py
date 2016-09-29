#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import auth
from actingweb import config

import webapp2
import logging

import os
from google.appengine.ext.webapp import template

from on_aw import on_aw_www_paths


class MainPage(webapp2.RequestHandler):

    def get(self, id, path):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='www', subpath=path)
        if not myself or check.response["code"] != 200:
            return
        if not Config.ui:
            self.response.set_status(404, "Web interface is not enabled")
            return
        if not check.checkAuthorisation(path='www', subpath=path, method='GET'):
            self.response.set_status(403)
            return

        if not path or path == '':
            template_values = {
                'url': self.request.url,
                'id': id,
                'creator': myself.creator,
                'passphrase': myself.passphrase,
            }
            template_path = os.path.join(os.path.dirname(
                __file__), 'templates/aw-actor-www-root.html')
            self.response.write(template.render(template_path, template_values).encode('utf-8'))
            return

        if path == 'init':
            template_values = {
                'id': myself.id,
            }
            template_path = os.path.join(os.path.dirname(
                __file__), 'templates/aw-actor-www-init.html')
            self.response.write(template.render(template_path, template_values).encode('utf-8'))
            return
        if path == 'properties':
            properties = myself.getProperties()
            template_values = {
                'id': myself.id,
                'properties': properties,
            }
            template_path = os.path.join(os.path.dirname(
                __file__), 'templates/aw-actor-www-properties.html')
            self.response.write(template.render(template_path, template_values).encode('utf-8'))
            return
        if path == 'property':
            lookup = myself.getProperty(self.request.get('name'))
            if lookup.value:
                template_values = {
                    'id': myself.id,
                    'property': lookup.name,
                    'value': lookup.value,
                    'qual': '',
                }
            else:
                template_values = {
                    'id': myself.id,
                    'property': lookup.name,
                    'value': 'Not set',
                    'qual': 'no',
                }
            template_path = os.path.join(os.path.dirname(
                __file__), 'templates/aw-actor-www-property.html')
            self.response.write(template.render(template_path, template_values).encode('utf-8'))
            return
        if path == 'trust':
            relationships = myself.getTrustRelationships()
            if not relationships:
                self.response.set_status(404, 'Not found')
                return
            trusts = []
            for t in relationships:
                trusts.append({
                    "peerid": t.peerid,
                    "relationship": t.relationship,
                    "type": t.type,
                    "approved": t.approved,
                    "approveuri": Config.root + myself.id + '/trust/' + t.relationship + '/' + t.peerid,
                    "peer_approved": t.peer_approved,
                    "baseuri": t.baseuri,
                    "desc": t.desc,
                    "verified": t.verified,
                }
                )
            template_values = {
                'id': myself.id,
                'trusts': trusts,
            }
            template_path = os.path.join(os.path.dirname(
                __file__), 'templates/aw-actor-www-trust.html')
            self.response.write(template.render(template_path, template_values).encode('utf-8'))
            return
        output = on_aw_www_paths.on_www_paths(myself, path)
        if output:
            self.response.write(output)
        else:
            self.response.set_status(404, "Not found")
        return

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/www<:/?><path:(.*)>', MainPage, name='MainPage'),
], debug=True)
