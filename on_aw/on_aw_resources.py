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
    Config = config.config()
    path = name.lower().split('/')
    if len(path) <= 1:
        return {}
    if path[0] == 'folders':
        folderId = path[1]
        boxLink = box.box(auth=auth, actorId=myself.id)
        folder = boxLink.getFolder(folder_id=folderId)
        if folder:
            return folder
    return {}


def on_delete_resources(myself, req, auth, name):
    """ Called on DELETE to resources. Return struct for json out.

        Returning {} will give a 404 response back to requestor. 
    """
    Config = config.config()
    path = name.lower().split('/')
    if len(path) <= 1:
        return {}
    if path[0] == 'folders':
        folderId = path[1]
        boxLink = box.box(auth=auth, actorId=myself.id)
        boxLink.cleanupFolder(folder_id=folderId)
        req.response.set_status(204)
        return 204
    return {}


def on_put_resources(myself, req, auth, name, params):
    """ Called on PUT to resources. Return struct for json out.

        Returning {} will give a 404 response back to requestor. 
        Returning an error code after setting the response will not change
        the error code.
    """
    Config = config.config()
    path = name.lower().split('/')
    if len(path) <= 1:
        return {}
    if path[0] == 'folders':
        folderId = path[1]
        if 'collaborations' not in params:
            req.response.set_status(405, "Mandatory parameter collaborations missing")
            return 405
        boxLink = box.box(auth=auth, actorId=myself.id)
        for collab in params['collaborations']:
            if 'email' not in collab:
                continue
            if 'role' in collab:
                role = collab['role']
            else:
                role = 'editor'
            if 'notify' in collab:
                notify = collab['notify']
            else:
                notify = False
            if 'action' in collab and collab['action'] == 'delete':
                if not boxLink.deleteCollaboration(folder_id=folderId, 
                                                   email=collab['email']):
                    logging.warn('Failed to delete collaboration user(' +
                                 collab['email'] + ') in folder(' +
                                 folderId + ')')
            else:
                if not boxLink.createCollaboration(folder_id=folderId,
                                                   email=collab['email'],
                                                   role=role,
                                                   notify=notify):
                    logging.warn('Failed to add collaboration user(' +
                                 collab['email'] +
                                 ') in folder(' +
                                 folderId + ')')
        req.response.set_status(200)
        return 200
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
            folder = boxLink.getFolder(name=foldername, parent=parent)
            pair = {
                'error': {
                    'code': auth.oauth.last_response_code,
                    'message': auth.oauth.last_response_message,
                },
            }
            if folder:
                pair['name'] = folder['name']
                pair['parent'] = folder['parentId']
                pair['id'] = folder['boxId']
                pair['url'] = folder['url']
            return pair
        url = boxLink.createLink(folder_id=folderid)
        if not url:
            url = ''
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
        req.response.headers.add_header("Location", str(Config.root + 'folders/' + folderid))
        pair = {
            'name': foldername,
            'parent': parent,
            'id': folderid,
            'emails': emails,
            'role': role,
            'notify': notify,
            'url': url,
        }
        return pair
    return {}


