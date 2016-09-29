#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import oauth
from actingweb import config

import webapp2
from google.appengine.ext import deferred


def on_aw_delete_actor(myself):
    # THIS METHOD IS CALLED WHEN AN ACTOR IS REQUESTED TO BE DELETED.
    # THE BELOW IS SAMPLE CODE
    # Clean up anything associated with this actor before it is deleted.
    #my_oauth=oauth.oauth(token = myself.getProperty('oauth_token').value)
    # END OF SAMPLE CODE
    return
