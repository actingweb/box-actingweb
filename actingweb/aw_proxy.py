import datetime
import time
import base64
import property
import urllib
from google.appengine.api import urlfetch
from google.appengine.ext import deferred
import json
import config
import trust
import subscription
import logging

__all__ = [
    'aw_proxy',
]


class aw_proxy():
    """ Proxy to other trust peers to execute RPC style calls

    Initialise with either trust_target to target a specific
    existing trust or use peer_target for simplicity to use
    the trust established with the peer. 
    """

    def __init__(self, trust_target=None, peer_target=None):
        self.last_response_code = 0
        self.last_response_message = 0
        self.last_location = None
        if trust_target and trust_target.trust:
            self.trust = trust_target
            self.actorid = trust_target.id
        elif peer_target and peer_target.actor:
            self.actorid = peer_target.actor.id
            self.trust = None
            if peer_target.peerid:
                self.trust = trust.trust(id=self.actorid, peerid=peer_target.peerid)
                if not self.trust or not self.trust.trust:
                    self.trust = None

    def getResource(self, path=None, params=None):
        if not path or len(path) == 0:
            return None
        if not params:
            params = {}
        if not self.trust or not self.trust.baseuri or not self.trust.secret:
            return None
        url = self.trust.baseuri.strip('/') + '/' + path.strip('/')
        if params:
            url = url + '?' + urllib.urlencode(params)
        headers = {'Authorization': 'Bearer ' + self.trust.secret,
                   }
        logging.debug(
            'Getting trust peer resource at (' + url + ')')
        try:
            response = urlfetch.fetch(url=url,
                                      method=urlfetch.GET,
                                      headers=headers
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            logging.debug('Not able to get peer resource')
            self.last_response_code = 408
            return {
                'error': {
                    'code': 408,
                    'message': 'Unable to communciate with trust peer service.',
                },
            }
        logging.debug('Get trust peer resource POST response:(' +
                      str(response.status_code) + ') ' + response.content)
        if response.status_code < 200 or response.status_code > 299:
            logging.warn('Not able to get trust peer resource.')
        try:
            result = json.loads(response.content)
        except:
            logging.debug("Not able to parse response when getting resource at(" + url + ")")
            result = {}
        return result

    def createResource(self, path=None, params=None):
        if not path or len(path) == 0:
            return None
        if not params:
            params = {}
        if not self.trust or not self.trust.baseuri or not self.trust.secret:
            return None
        data = json.dumps(params)
        headers = {'Authorization': 'Bearer ' + self.trust.secret,
                   'Content-Type': 'application/json',
                   }
        url = self.trust.baseuri.strip('/') + '/' + path.strip('/')
        logging.debug(
            'Creating trust peer resource at (' + url + ') with data(' +
            str(data) + ')')
        try:
            response = urlfetch.fetch(url=url,
                                      method=urlfetch.POST,
                                      payload=data,
                                      headers=headers
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            logging.debug('Not able to create new peer resource')
            self.last_response_code = 408
            return {
                'error': {
                    'code': 408,
                    'message': 'Unable to communciate with trust peer service.',
                },
            }
        if 'Location' in response.headers:
            self.last_location = response.headers['Location']
        else:
            self.last_location = None
        logging.debug('Create trust peer resource POST response:(' +
                      str(response.status_code) + ') ' + response.content)
        if response.status_code < 200 or response.status_code > 299:
            logging.warn('Not able to create new trust peer resource.')
        try:
            result = json.loads(response.content)
        except:
            logging.debug("Not able to parse response when creating resource at(" + url + ")")
            result = {}
        return result

    def changeResource(self, path=None, params=None):
        if not path or len(path) == 0:
            return None
        if not params:
            params = {}
        if not self.trust or not self.trust.baseuri or not self.trust.secret:
            return None
        data = json.dumps(params)
        headers = {'Authorization': 'Bearer ' + self.trust.secret,
                   'Content-Type': 'application/json',
                   }
        url = self.trust.baseuri.strip('/') + '/' + path.strip('/')
        logging.debug(
            'Changing trust peer resource at (' + url + ') with data(' +
            str(data) + ')')
        try:
            response = urlfetch.fetch(url=url,
                                      method=urlfetch.PUT,
                                      payload=data,
                                      headers=headers
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            logging.debug('Not able to change peer resource')
            self.last_response_code = 408
            return {
                'error': {
                    'code': 408,
                    'message': 'Unable to communciate with trust peer service.',
                },
            }
        logging.debug('Change trust peer resource PUT response:(' +
                      str(response.status_code) + ') ' + response.content)
        if response.status_code < 200 or response.status_code > 299:
            logging.warn('Not able to change trust peer resource.')
        try:
            result = json.loads(response.content)
        except:
            logging.debug("Not able to parse response when changing resource at(" + url + ")")
            result = {}
        return result

    def deleteResource(self, path=None):
        if not path or len(path) == 0:
            return None
        if not self.trust or not self.trust.baseuri or not self.trust.secret:
            return None
        headers = {'Authorization': 'Bearer ' + self.trust.secret,
                   }
        url = self.trust.baseuri.strip('/') + '/' + path.strip('/')
        logging.debug(
            'Deleting trust peer resource at (' + url + ')')
        try:
            response = urlfetch.fetch(url=url,
                                      method=urlfetch.DELETE,
                                      headers=headers
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            logging.debug('Not able to delete peer resource')
            self.last_response_code = 408
            return {
                'error': {
                    'code': 408,
                    'message': 'Unable to communciate with trust peer service.',
                },
            }
        logging.debug('Delete trust peer resource POST response:(' +
                      str(response.status_code) + ') ' + response.content)
        if response.status_code < 200 or response.status_code > 299:
            logging.warn('Not able to delete trust peer resource.')
            return False
        return True
