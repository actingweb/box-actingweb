#!/usr/bin/env python
#
from actingweb import actor
from actingweb import oauth
from actingweb import config
from google.appengine.ext import deferred

import logging
import json
import os
import time
from google.appengine.ext.webapp import template


__all__ = [
    'on_post_callbacks',
    'on_get_callbacks',
    'on_post_subscriptions',
    'on_delete_callbacks',
]


def on_get_callbacks(myself, req, name):
    """Customizible function to handle GET /callbacks"""
    # return True if callback has been processed
    # THE BELOW IS SAMPLE CODE
    #my_oauth=oauth.oauth(token = myself.getProperty('oauth_token').value)
    # if name == 'something':
    #    return
    # END OF SAMPLE CODE
    return False


def on_delete_callbacks(myself, req, name):
    """Customizible function to handle DELETE /callbacks"""
    # return True if callback has been processed
    return False


def on_post_callbacks(myself, req, auth, name):
    """Customizible function to handle POST /callbacks"""
    Config = config.config()
    logging.debug("Callback body: "+req.request.body.decode('utf-8', 'ignore'))
    try:
        body = json.loads(req.request.body.decode('utf-8', 'ignore'))
    except:
        return False
    path = name.split('/')
    if path[0] == 'box':
        trigger = 'Unknown'
        filename = 'Unknown'
        if 'trigger' in body:
            trigger = body['trigger']
        if 'source' in body and 'name' in body['source']:
            filename = body['source']['name']
        logging.debug('Got trigger(' + trigger + ') with filename(' + filename + ')')
        req.response.set_status(204)
        return True
    req.response.set_status(404, "Callback not found.")
    return False


def on_post_subscriptions(myself, req, auth, sub, peerid, data):
    """Customizible function to process incoming callbacks/subscriptions/ callback with json body, return True if processed, False if not."""
    logging.debug("Got callback and processed " + sub.subid +
                  " subscription from peer " + peerid + " with json blob: " + json.dumps(data))
    return True
