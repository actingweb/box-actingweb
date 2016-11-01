#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import oauth
from actingweb import config
from box import box

import webapp2
from google.appengine.ext import deferred


def on_aw_delete_actor(myself, req, auth):
    boxLink = box.box(auth=auth, actorId=myself.id)
    boxLink.cleanupAllFolders()
    return
