#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import oauth
from actingweb import config

import webapp2
from google.appengine.ext import deferred


def on_aw_delete_actor(myself, req, auth):
    # THIS METHOD IS CALLED WHEN AN ACTOR IS REQUESTED TO BE DELETED.
    # THE BELOW IS SAMPLE CODE
    # Clean up anything associated with this actor before it is deleted.
    # END OF SAMPLE CODE
    return
