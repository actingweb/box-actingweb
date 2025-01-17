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
        filename = 'Not Available'
        foldername = 'Not Available'
        file_id = None
        folder_id = None
        user = 'Unknown'
        message = ''
        if 'trigger' in body:
            trigger = body['trigger']
        if 'source' in body:
            if 'type' in body['source']:
                if body['source']['type'] == 'file'  and 'name' in body['source']:
                    filename = body['source']['name']
                elif body['source']['type'] == 'file'  and 'id' in body['source']:
                    file_id = body['source']['id']
                if body['source']['type'] == 'folder'  and 'name' in body['source']:
                    foldername = body['source']['name']
                elif body['source']['type'] == 'folder'  and 'id' in body['source']:
                    folder_id = body['source']['id']
                if body['source']['type'] == 'comment'  and 'message' in body['source']:
                    message = body['source']['message']
                    if 'item' in body['source'] and 'type' in body['source']['item']:
                        if body['source']['item']['type'] == 'file':
                            file_id = body['source']['item']['id']
                        elif body['source']['item']['type'] == 'folder':
                            folder_id = body['source']['item']['id']
        if 'created_by' in body:
            if 'name' in body['created_by']:
                user = body['created_by']['name']
        boxLink = box.box(auth=auth, actorId=myself.id)
        if file_id and (trigger != 'FILE.TRASHED' and trigger != 'FILE.DELETED'):
            file = boxLink.getBoxFile(id=file_id)
            if file and 'name' in file:
                filename = file['name']
        if folder_id and (trigger != 'FOLDER.TRASHED' and trigger != 'FOLDER.DELETED'):
            folder = boxLink.getBoxFolder(id=folder_id)
            if folder and 'name' in folder:
                foldername = folder['name']
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
        elif trigger == 'COMMENT.CREATED':
            txt = user + ' commented on the file named: ' + filename + ' - ' + message
        elif trigger == 'COMMENT.UPDATED':
            txt = user + ' updated comment on the file named: ' + filename + ' - ' + message
        elif trigger == 'COMMENT.DELETED':
            txt = user + ' deleted comment on the file named: ' + filename + ' - ' + message
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
        if len(message) > 0:
            params['message'] = message
        if body and 'webhook' in body and 'id' in body['webhook']:
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
