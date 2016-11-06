#!/usr/bin/env python
#
from actingweb import actor
from actingweb import oauth
from actingweb import config
from box import box
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
        trigger = ''
        filename = ''
        foldername = ''
        user = 'Unknown'
        if 'trigger' in body:
            trigger = body['trigger']
        if 'source' in body:
            if 'type' in body['source']:
                if body['source']['type'] == 'file'  and 'name' in body['source']:
                    filename = body['source']['name']
                if body['source']['type'] == 'folder'  and 'name' in body['source']:
                    foldername = body['source']['name']
        if 'created_by' in body:
            if 'name' in body['created_by']:
                user = body['created_by']['name']
        logging.debug('Got trigger(' + trigger + ') for (file:' + filename + '/folder:' + foldername + ') by user ' + user)
        if trigger == 'FILE.UPLOADED':
            txt = user + ' uploaded a new file named: ' + filename
        elif trigger == 'FILE.TRASHED':
            txt = user + ' trashed a file named: ' + filename
        elif trigger == 'FILE.DELETED':
            txt = user + ' deleted a file named: ' + filename
        elif trigger == 'FILE.RESTORED':
            txt = user + ' restored a file named: ' + filename
        elif trigger == 'FILE.MOVED':
            txt = user + ' moved a file named: ' + filename
        elif trigger == 'FILE.LOCKED':
            txt = user + ' locked the file named: ' + filename
        elif trigger == 'FILE.UNLOCKED':
            txt = user + ' unlocked the file named: ' + filename
        elif trigger == 'FOLDER.CREATED':
            txt = user + ' created a new folder named: ' + foldername
        elif trigger == 'FOLDER.DELETED':
            txt = user + ' deleted a folder named: ' + foldername
        elif trigger == 'FOLDER.RESTORED':
            txt = user + ' restored a folder named: ' + foldername
        elif trigger == 'FOLDER.TRASHED':
            txt = user + ' trashed a folder named: ' + foldername
        elif trigger == 'FOLDER.MOVED':
            txt = user + ' moved a folder named: ' + foldername
        elif trigger == 'WEBHOOK.DELETED':
            txt = user + ' deleted the root folder named: ' + foldername
        params = {
            'trigger': trigger,
            'user': user,
            'suggested_txt': txt,
            'data': body,
        }
        if len(filename) > 0:
            params['name'] = filename
        elif len(foldername) > 0:
            params['name'] = foldername
        if body and 'webhook' in body and 'id' in body['webhook']:
            boxLink = box.box(auth=auth, actorId=myself.id)
            hook = boxLink.getWebhook(id=body['webhook']['id'])
            if hook and hook.folderId:
                blob = json.dumps(params)
                myself.registerDiffs(
                    target='resources',
                    subtarget='folders',
                    resource=hook.folderId,
                    blob=blob)
        req.response.set_status(204)
        return True
    req.response.set_status(404, "Callback not found.")
    return False


def on_post_subscriptions(myself, req, auth, sub, peerid, data):
    """Customizible function to process incoming callbacks/subscriptions/ callback with json body, return True if processed, False if not."""
    logging.debug("Got callback and processed " + sub.subid +
                  " subscription from peer " + peerid + " with json blob: " + json.dumps(data))
    return True
