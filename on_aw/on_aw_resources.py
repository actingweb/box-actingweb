#!/usr/bin/env python
import webapp2
import logging
import time
from google.appengine.ext import deferred
from actingweb import actor
from actingweb import oauth
from actingweb import config
from box import box

__all__ = [
    'on_post_resources',
    'on_get_resources',
    'on_delete_resources',
]


def on_get_resources(myself, req, auth, name, params):
    """ Called on GET to resources. Return struct for json out.

        Returning {} will give a 404 response back to requestor. 
    """
    return {}


def on_delete_resources(myself, req, auth, name, params):
    """ Called on DELETE to resources. Return struct for json out.

        Returning {} will give a 404 response back to requestor. 
    """
    return {}


def on_post_resources(myself, req, auth, name, params):
    """ Called on POST to resources. Return struct for json out.

        Returning {} will give a 404 response back to requestor. 
        Returning an error code after setting the response will not change
        the error code.
    """
    Config = config.config()
    if name == 'folders':
        if 'name' in params:
            foldername = params['name']
        else:
            self.response.set_status(405, 'Missing mandatory parameter')
            return
        if 'parent' in params:
            parent = params['parent']
        else:
            parent = '0'
        boxLink = box.box(auth=auth, actorId=myself.id)
        folderid = boxLink.createFolder(foldername, parent)
        if not folderid:
            req.response.set_status(408, "Failed creating folder in box")
            return 408
        if 'role' in params:
            role = params['role']
        else:
            role = 'editor'
        if 'notify' in params:
            notify = params['notify']
        else:
            notify = False
        if 'emails' in params:
            emails = params['emails']
            boxLink.addUserAccess(folder_id=folderid,
                                  emails=emails,
                                  role=role,
                                  notify=notify)
        else:
            emails = {}
        boxLink.createWebhook(folder_id=folderid, 
                              callback=Config.root + myself.id + '/callbacks/box/' + folderid)
        pair = {
            'name': foldername,
            'parent': parent,
            'id': folderid,
            'emails': emails,
            'role': role,
            'notify': notify,
        }
        return pair
    return {}


