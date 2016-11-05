from db import db
import datetime
import time
import urllib
from google.appengine.api import urlfetch
from google.appengine.ext import deferred
import json
import config
import logging

__all__ = [
    'peerTrustee',
]


class peerTrustee():

    def __init__(self, actor=None, shorttype=None, peerid=None):
        if actor and actor.id:
            self.actor = actor
        else:
            self.actor = None
        self.shorttype = shorttype
        self.fresh = False
        self.peerid = peerid
        self.get(peerid=peerid, shorttype=shorttype)

    def get(self, peerid=None, shorttype=None):
        result = None
        if peerid:
            result = db.PeerTrustee.query(db.PeerTrustee.id == self.actor.id,
                                   db.PeerTrustee.peerid == peerid).get(use_cache=False)
        elif shorttype:
            Config = config.config()
            if not Config.actors[shorttype]:
                logging.error('Got request to get peer with unknown shorttype(' + shorttype + ')')
                return False
            result = db.PeerTrustee.query(db.PeerTrustee.id == self.actor.id,
                                   db.PeerTrustee.type == Config.actors[shorttype]['type']).fetch(use_cache=False)
            if len(result) > 1:
                logging.error('Found more than one peer of this type(' + 
                              shorttype + '). Unable to determine which, need peerid lookup.')
                return False
            if len(result) == 1:
                result = result[0]
        if result:
            self.peer = result
            self.peerid = result.peerid
            self.baseuri = result.baseuri
            self.type = result.type
            self.passphrase = result.passphrase
        else:
            self.peer = None
            self.peerid = None
            self.baseuri = None
            self.type = None
            self.passphrase = None

    def create(self, peerid='', baseuri='', type='', passphrase=''):
        if len(peerid) == 0 or len(baseuri) == 0 or len(type) == 0:
            return False
        if self.peer:
            self.peer.id = self.actor.id
            self.peer.peerid = peerid
            self.peer.baseuri = baseuri
            self.peer.type = type
            self.passphrase = passphrase
        else:
            self.peer = db.PeerTrustee(id=self.actor.id,
                                       peerid=peerid,
                                       baseuri=baseuri,
                                       type=type,
                                       passphrase=passphrase)
        self.peer.put(use_cache=False)
        self.fresh = True
        self.peerid = peerid
        self.baseuri = baseuri
        self.type = type
        self.passphrase = passphrase
        return True

    def delete(self):
        if not self.peer:
            return False
        self.peer.key.delete(use_cache=False)
        return True
