import urllib
import logging
import json
from google.appengine.api import urlfetch

import config

__all__ = [
    'oauth',
]

# This function code is from latest urlfetch. For some reason the
# Appengine version of urlfetch does not include links()


def PaginationLinks(self):
    """Links parsed from HTTP Link header"""
    ret = []
    if 'link' in self.headers:
        linkheader = self.headers['link']
    else:
        return ret
    for i in linkheader.split(','):
        try:
            url, params = i.split(';', 1)
        except ValueError:
            url, params = i, ''
        link = {}
        link['url'] = url.strip('''<> '"''')
        for param in params.split(';'):
            try:
                k, v = param.split('=')
            except ValueError:
                break
            link[k.strip(''' '"''')] = v.strip(''' '"''')
        ret.append(link)
    return ret


class oauth():

    def __init__(self, token=None):
        Config = config.config()
        self.config = Config.oauth
        self.token = token
        self.first = None
        self.next = None
        self.prev = None
        self.last_response_code = 0
        self.last_response_message = ""

    def enabled(self):
        if len(self.config['client_id']) == 0:
            return False
        else:
            return True

    def setToken(self, token):
        if token:
            self.token = token

    def postRequest(self, url, params=None, cleartoken=False, urlencode=False):
        if cleartoken:
            self.token = None
        if params:
            if urlencode:
                data = urllib.urlencode(params)
                logging.info('Oauth POST request with urlencoded payload: ' + url + ' ' + data)
            else:
                data = json.dumps(params)
                logging.info('Oauth POST request with JSON payload: ' + url + ' ' + data)
        else:
            data = None
            logging.info('Oauth POST request: ' + url)
        if urlencode:
            if self.token:
                headers = {'Content-Type': 'application/x-www-form-urlencoded',
                           'Authorization': 'Bearer ' + self.token,
                           }
            else:
                headers = {'Content-Type': 'application/x-www-form-urlencoded',
                           }
        else:
            if self.token:
                headers = {'Content-Type': 'application/json',
                           'Authorization': 'Bearer ' + self.token,
                           }
            else:
                headers = {'Content-Type': 'application/json'}
        try:
            urlfetch.set_default_fetch_deadline(20)
            response = urlfetch.fetch(url=url, payload=data, method=urlfetch.POST, headers=headers)
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            logging.warn("Spark POST failed with exception")
            return False
        if response.status_code == 204:
            return True
        if response.status_code != 200:
            logging.info('Error when sending POST request: ' +
                         str(response.status_code) + response.content)
            return False
        logging.debug('Oauth POST response JSON:' + response.content)
        return json.loads(response.content)

    def getRequest(self, url, params=None):
        if not self.token:
            logging.debug("No token set in getRequest()")
            return None
        if params:
            url = url + '?' + urllib.urlencode(params)
        logging.info('Oauth GET request: ' + url)
        urlfetch.set_default_fetch_deadline(60)
        try:
            response = urlfetch.fetch(url=url,
                                      method=urlfetch.GET,
                                      headers={'Authorization': 'Bearer ' + self.token}
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            logging.warn("Spark GET failed with exception")
            return None
        if response.status_code < 200 or response.status_code > 299:
            logging.info('Error when sending GET request to Oauth: ' +
                         str(response.status_code) + response.content)
            return None
        links = PaginationLinks(response)
        self.next = None
        self.first = None
        self.prev = None
        for link in links:
            logging.debug('Links:' + link['rel'] + ':' + link['url'])
            if link['rel'] == 'next':
                self.next = link['url']
            elif link['rel'] == 'first':
                self.first = link['url']
            elif link['rel'] == 'prev':
                self.prev = link['url']
        return json.loads(response.content)

    def deleteRequest(self, url):
        if not self.token:
            return None
        logging.info('Oauth DELETE request: ' + url)
        try:
            response = urlfetch.fetch(url=url,
                                      method=urlfetch.DELETE,
                                      headers={'Authorization': 'Bearer ' + self.token}
                                      )
            self.last_response_code = response.status_code
            self.last_response_message = response.content
        except:
            logging.warn("Spark DELETE failed.")
        if response.status_code < 200 and response.status_code > 299:
            logging.info('Error when sending DELETE request to Oauth: ' +
                         str(response.status_code) + response.content)
            return False
        if response.status_code == 204:
            return True
        return json.loads(response.content)

    def oauthRedirectURI(self, state=''):
        params = {
            'response_type': self.config['response_type'],
            'client_id': self.config['client_id'],
            'redirect_uri': self.config['redirect_uri'],
            'scope': self.config['scope'],
            'state': state,
        }
        uri = self.config['auth_uri'] + "?" + urllib.urlencode(params)
        logging.info('OAuth redirect with url: ' + uri + ' and state:' + state)
        return uri

    def oauthRequestToken(self, code=None):
        if not code:
            return None
        params = {
            'grant_type': self.config['grant_type'],
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'code': code,
            'redirect_uri': self.config['redirect_uri'],
        }
        result = self.postRequest(url=self.config[
                                  'token_uri'], cleartoken=True, params=params, urlencode=True)
        if result and 'access_token' in result:
            self.token = result['access_token']
        return result

    def oauthRefreshToken(self, refresh_token):
        if not refresh_token:
            return None
        params = {
            'grant_type': self.config['refresh_type'],
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'refresh_token': refresh_token,
        }
        result = self.postRequest(url=self.config[
                                  'token_uri'], cleartoken=True, params=params, urlencode=True)
        if not result:
            self.token = None
            return False
        self.token = result['access_token']
        return result
