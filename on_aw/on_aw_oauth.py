#!/usr/bin/env python
import webapp2
import logging
import time
from google.appengine.ext import deferred
from actingweb import actor
from actingweb import oauth
from actingweb import config

__all__ = [
    'check_on_oauth_success',
]


def check_on_oauth_success(myself, req, auth, token=None):
    # THIS METHOD IS CALLED WHEN AN OAUTH AUTHORIZATION HAS BEEN SUCCESSFULLY MADE
    return True
