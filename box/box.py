import logging
from google.appengine.ext import ndb

__all__ = [
    'box',
]


class Folder(ndb.Model):
    actorId = ndb.StringProperty(required=True)
    boxId = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    parentId = ndb.StringProperty(required=True)
    url = ndb.StringProperty()


class Collaboration(ndb.Model):
    actorId = ndb.StringProperty(required=True)
    boxId = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    userId = ndb.StringProperty(required=True)
    folderId = ndb.StringProperty(required=True)
    role = ndb.StringProperty(required=True)


class Webhook(ndb.Model):
    actorId = ndb.StringProperty(required=True)
    boxId = ndb.StringProperty(required=True)
    folderId = ndb.StringProperty(required=True)


class box():

    def __init__(self, auth, actorId):
        self.actorId = actorId
        self.auth = auth
        self.box = {
            'folder_uri': "https://api.box.com/2.0/folders/",
            'collaboration_uri': "https://api.box.com/2.0/collaborations/",
            'webhook_uri': "https://api.box.com/2.0/webhooks/",
        }

    def lastResponse(self, what=''):
        if what == 'code':
            return self.auth.oauth.last_response_code
        if what == 'message':
            self.auth.oauth.last_response_message
        return {
            'code': self.auth.oauth.last_response_code,
            'message': self.auth.oauth.last_response_message,
        }

    def cleanupAllFolders(self):
        folders = Folder.query(Folder.actorId == self.actorId
                    ).fetch(use_cache=False)
        if not folders:
            return False
        for folder in folders:
            self.cleanupFolder(folder_id=folder.boxId)
        return True

    def cleanupFolder(self, folder_id=None):
        """ Delete webhook @ box, just clean db for folder & collabs."""
        if not folder_id:
            return False
        self.deleteWebhook(folder_id=folder_id)
        folder = Folder.query(Folder.actorId == self.actorId,
                                Folder.boxId == folder_id
                                ).get(use_cache=False)
        if not folder:
            return False
        folder.key.delete(use_cache=False)
        collabs = Collaboration.query(
                    Collaboration.actorId == self.actorId,
                    Collaboration.folderId == folder_id
                    ).fetch(use_cache=False)
        for collab in collabs:
            collab.key.delete(use_cache=False)
        return True

    def getFolders(self):
        folders = Folder.query(Folder.actorId == self.actorId
                    ).fetch(use_cache=False)
        if not folders:
            return None
        ret = []
        for folder in folders:
            ret.append(self.getFolder(folder.boxId))
        return ret

    def getFolder(self, name=None, folder_id=None, parent='0'):
        if not name and not folder_id:
            return None
        if folder_id:
            folder = Folder.query(Folder.actorId == self.actorId,
                                  Folder.boxId == folder_id,
                                  Folder.parentId == parent
                                  ).get(use_cache=False)
        else:
            folder = Folder.query(Folder.actorId == self.actorId,
                                  Folder.name == name,
                                  Folder.parentId == parent
                                  ).get(use_cache=False)
        if not folder:
            return False
        ret = {
            'boxId': folder.boxId,
            'name' : folder.name,
            'parentId' : folder.parentId,
            'url' : folder.url,
        }
        collabs = Collaboration.query(
                    Collaboration.actorId == self.actorId,
                    Collaboration.folderId == ret['boxId']
                    ).fetch(use_cache=False)
        ret['users'] = []
        for collab in collabs:
            ret['users'].append({
                'email': collab.email,
                'collabBoxId': collab.boxId,
                'userBoxId': collab.userId,
                'role': collab.role,
            })
        hook = Webhook.query(
                Webhook.actorId == self.actorId,
                Webhook.folderId == ret['boxId']
                ).get(use_cache=False)
        if hook:
            ret['webhookId'] = hook.boxId
        return ret

    def createLink(self, folder_id=None, level='collaborators'):
        """ Creates a box folder shared link and returns url or None """
        if not folder_id:
            return None
        folder = Folder.query(Folder.actorId == self.actorId,
                              Folder.boxId == folder_id,
                              ).get(use_cache=False)
        if not folder:
            return None
        params = {
            'shared_link': {'access': level},
        }
        ret = self.auth.oauthPUT(url=self.box['folder_uri'] + folder_id, params=params)
        if self.lastResponse('code') != 200:
            return None
        if 'shared_link' in ret and ret['shared_link'] and 'url' in ret['shared_link']:
            folder.url = ret['shared_link']['url']
            folder.put(use_cache=False)
            return folder.url
        else:
            return None

    def createFolder(self, name=None, parent='0'):
        """ Creates a box folder and returns the box id or None """
        if not name:
            return None
        if self.getFolder(name=name, parent=parent):
            self.auth.oauth.last_response_code = 409
            self.auth.oauth.last_response_message = 'The folder already exists.'
            return None
        params = {
            'name': name,
            'parent': {'id': parent},
        }
        ret = self.auth.oauthPOST(url=self.box['folder_uri'], params=params)
        if self.lastResponse('code') == 409:
            self.auth.oauth.last_response_message = 'The folder already exists.'
        if self.lastResponse('code') != 201 or not ret:
            return None
        if 'shared_link' in ret and ret['shared_link'] and 'url' in ret['shared_link']:
            url = ret['shared_link']['url']
        else:
            url = ''
        dbfolder = Folder(actorId=self.actorId, 
                          boxId=ret['id'],
                          name=name,
                          parentId=parent,
                          url=url)
        dbfolder.put()
        return ret['id']

    def deleteCollaboration(self, folder_id=None, email=None):
        if not folder_id or not email:
            return False
        collab = Collaboration.query(
                    Collaboration.actorId == self.actorId,
                    Collaboration.email == email,
                    Collaboration.folderId == folder_id).get()
        if not collab:
            return False
        ret = self.auth.oauthDELETE(url=self.box['collaboration_uri'] + collab.boxId)
        if self.lastResponse('code') != 204:
            logging.debug('Unable to delete collaboration for user(' +
                          email + ') on folder(' + folder_id + ')')
            return False
        collab.key.delete()
        return True

    def createCollaboration(self, folder_id=None, email=None, role=None, 
                            notify=None):
        if not folder_id or not email:
            return False
        if not role:
            role = 'editor'
        if not notify:
            notify = False
        params = {
            'item': {
                'id': folder_id,
                'type': 'folder',
                },
            'notify': notify,
            'role': role,
            'accessible_by': {
                'login': email,
                'type': 'user',
                },
        }
        ret = self.auth.oauthPOST(url=self.box['collaboration_uri'], params=params)
        if self.lastResponse('code') != 201:
            return False
        if 'accessible_by' in ret and ret['accessible_by'] and 'id' in ret['accessible_by']:
            userId = ret['accessible_by']['id']
        else:
            userId = '0'
        dbCollaboration = Collaboration(actorId=self.actorId,
                                        boxId=ret['id'],
                                        userId=userId,
                                        email=email,
                                        folderId=folder_id,
                                        role=role)
        dbCollaboration.put()
        return ret['id']

    def addUserAccess(self, folder_id=None, emails=None, role=None, notify=None):
        if not folder_id or not emails:
            return False
        if not role:
            role = 'editor'
        if not notify:
            notify = False
        for email in emails:
            if not self.createCollaboration(folder_id=folder_id, email=email,
                                            role=role, notify=notify):
                logging.warn('Was not able to add ' + email +
                             ' to access list for folder(' + folder_id + ')')

    def deleteWebhook(self, folder_id=None):
        if not folder_id:
            return False
        hook = Webhook.query(
                Webhook.actorId == self.actorId,
                Webhook.folderId == folder_id).get()
        if not hook:
            return False
        ret = self.auth.oauthDELETE(url=self.box['webhook_uri'] + hook.boxId)
        if self.lastResponse('code') != 204:
            logging.warn('Failed to delete webhook for folder(' + folder_id + ')')
            return False
        hook.key.delete()
        return True

    def createWebhook(self, folder_id=None, triggers=None, callback=None):
        if not folder_id or not callback:
            return False
        if not triggers:
            triggers = [
                "FILE.UPLOADED",
                "FILE.TRASHED",
                "FILE.DELETED",
                "FILE.RESTORED",
                "FILE.MOVED",
                "FILE.LOCKED",
                "FILE.UNLOCKED",
                "FOLDER.CREATED",
                "FOLDER.DELETED",
                "FOLDER.MOVED",
            ]
        params = {
            'target': {
                'id': folder_id,
                'type': 'folder',
                },
            'address': callback,
            'triggers': triggers,
        }
        ret = self.auth.oauthPOST(url=self.box['webhook_uri'], params=params)
        if self.lastResponse('code') != 201:
            logging.warn('Failed to create webhook for folder(' + folder_id + ')')
            return False
        dbWebhook = Webhook(actorId=self.actorId,
                            boxId=ret['id'],
                            folderId=folder_id)
        dbWebhook.put()
        return ret['id']
