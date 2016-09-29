import actor
from db import db
import datetime
import config
import logging

__all__ = [
    'trust',
]


class trust():

    def get(self, id, peerid):
        result = db.Trust.query(db.Trust.id == id, db.Trust.peerid == peerid).get(use_cache=False)
        if result:
            self.trust = result
            self.id = id
            self.baseuri = result.baseuri
            self.secret = result.secret
            self.desc = result.desc
            self.peerid = result.peerid
            self.type = result.type
            self.relationship = result.relationship
            self.approved = result.approved
            self.peer_approved = result.peer_approved
            self.verified = result.verified
            self.verificationToken = result.verificationToken
        else:
            self.id = id
            self.peerid = peerid
            self.trust = None
            self.approved = False
            self.peer_approved = False
            self.verified = False

    def getByToken(self, token):
        result = db.Trust.query(db.Trust.id == self.id, db.Trust.secret ==
                                token).get(use_cache=False)
        if result:
            self.trust = result
            self.id = id
            self.baseuri = result.baseuri
            self.secret = result.secret
            self.desc = result.desc
            self.peerid = result.peerid
            self.type = result.type
            self.relationship = result.relationship
            self.approved = result.approved
            self.peer_approved = result.peer_approved
            self.verified = result.verified
            self.verificationToken = result.verificationToken
        else:
            self.id = id
            self.peerid = None
            self.trust = None
            self.approved = False
            self.peer_approved = False
            self.verified = False

    def delete(self):
        if not self.trust:
            self.get(self.id, self.peerid)
        if not self.trust:
            return False
        self.trust.key.delete(use_cache=False)

    def modify(self, baseuri='', secret='', desc='', approved=None, verified=None, verificationToken=None, peer_approved=None):
        if not self.trust:
            return False
        change = False
        if len(baseuri) > 0:
            change = True
            self.baseuri = baseuri
            self.trust.baseuri = baseuri
        if len(secret) > 0:
            change = True
            self.secret = secret
            self.trust.secret = secret
        if len(desc) > 0:
            change = True
            self.desc = desc
            self.trust.desc = desc
        if approved is not None:
            change = True
            self.approved = approved
            self.trust.approved = approved
        if verified is not None:
            change = True
            self.verified = verified
            self.trust.verified = verified
        if verificationToken is not None:
            change = True
            self.verificationToken = verificationToken
            self.trust.verificationToken = verificationToken
        if peer_approved is not None:
            change = True
            self.peer_approved = peer_approved
            self.trust.peer_approved = peer_approved
        if not change:
            return False
        self.trust.put(use_cache=False)
        return True

    def create(self, baseuri='', type='', relationship='', secret='', approved=False, verified=False, verificationToken='', desc='', peer_approved=False):
        if self.trust:
            return False
        self.baseuri = baseuri
        self.type = type
        Config = config.config()
        if not relationship or len(relationship) == 0:
            self.relationship = Config.default_relationship
        else:
            self.relationship = relationship
        if not secret or len(secret) == 0:
            self.secret = Config.newToken()
        else:
            self.secret = secret
        # Be absolutely sure that the secret is not already used
        result = db.Trust.query(db.Trust.id == self.id, db.Trust.secret == secret).get(use_cache=False)
        if result:
            return False
        self.approved = approved
        self.peer_approved = peer_approved
        self.verified = verified
        if not verificationToken or len(verificationToken) == 0:
            self.verificationToken = Config.newToken()
        if not desc:
            desc = ''
        self.desc = desc
        self.trust = db.Trust(id=self.id,
                                peerid=self.peerid,
                                baseuri=self.baseuri,
                                type=self.type,
                                relationship=self.relationship,
                                secret=self.secret,
                                approved=self.approved,
                                verified=self.verified,
                                peer_approved=self.peer_approved,
                                verificationToken=self.verificationToken,
                                desc=self.desc)
        self.trust.put(use_cache=False)
        return True

    def __init__(self, id, peerid=None, token=None):
        self.last_response_code = 0
        self.last_response_message = ''
        if not id or len(id) == 0:
            self.trust = None
            return
        if (not peerid or len(peerid) == 0) and (not token or len(token) == 0):
            self.trust = None
            return
        if token and len(token) > 0:
            self.id = id
            self.getByToken(token)
        else:
            self.get(id, peerid)
