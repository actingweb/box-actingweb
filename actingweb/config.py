__all__ = [
    'config',
]

import uuid
import binascii
import os
import logging


class config():

    def __init__(self):
        #########
        # Basic settings for this app
        #########
        self.ui = True                                      # Turn on the /www path
        self.www_auth = "oauth"                             # basic or oauth: basic for creator + bearer tokens
        self.fqdn = "box-spark-dev.appspot.com"         # The host and domain, i.e. FQDN, of the URL
        self.devtest = True                                 # Enable /devtest path for test purposes, MUST be False in production
        self.proto = "https://"                             # http or https
        self.logLevel = logging.DEBUG  # Change to WARN for production, DEBUG for debugging, and INFO for normal testing
        #########
        # ActingWeb settings for this app
        #########
        self.type = "urn:actingweb:actingweb.org:boxbasic"  # The app type this actor implements
        self.desc = "Box actor: "                           # A human-readable description for this specific actor
        self.version = "1.0"                                # A version number for this app
        self.info = "http://actingweb.org/"                 # Where can more info be found
        self.aw_version = "0.9"                             # This app follows the actingweb specification specified
        self.aw_supported = "www,oauth,callbacks"           # This app supports the following options
        self.specification = ""                             # URL to a RAML/Swagger etc definition if available
        self.aw_formats = "json"                            # These are the supported formats
        #########
        # Known and trusted ActingWeb actors
        #########
        self.actors = {
            '<SHORTTYPE>': {
                'type': 'urn:<ACTINGWEB_TYPE>',
                'factory': '<ROOT_URI>',
                'relationship': 'friend',                   # associate, friend, partner, admin
                },
            'myself': {
                'type': self.type,
                'factory': self.proto + self.fqdn + '/',
                'relationship': 'friend',                   # associate, friend, partner, admin
                },
        }
        #########

        # OAuth settings for this app, fill in if OAuth is used
        #########
        self.oauth = {
            'client_id': "eirmvll7oq3cwgsbcyteckzirp4jc3x8",                                # An empty client_id turns off oauth capabilities
            'client_secret': "HdThSTk8bf36Mjx0PE7MzzotYJjCko9T",
            'redirect_uri': self.proto + self.fqdn + "/oauth",
            'scope': "",
            'auth_uri': "https://account.box.com/api/oauth2/authorize",
            'token_uri': "https://api.box.com/oauth2/token",
            'response_type': "code",
            'grant_type': "authorization_code",
            'refresh_type': "refresh_token",
        }
        self.bot = {
            'token': '',
            'email': '',
        }
        #########
        # Trust settings for this app
        #########
        self.default_relationship = "associate"                # Default relationship if not specified
        self.auto_accept_default_relationship = False          # True if auto-approval
        # List of paths and their access levels
        # Matching is done top to bottom stopping at first match (role, path)
        # If no match is found on path with the correct role, access is rejected
        # <type> and <id> are used as templates for trust types and ids
        self.access = [
            # (role, path, method, access), e.g. ('friend', '/properties', '', 'rw')
            # Roles: creator, trustee, associate, friend, partner, admin, any (i.e. authenticated),
            #        owner (i.e. trust peer owning the entity)
            #        + any other new role for this app
            # Methods: GET, POST, PUT, DELETE
            # Access: a (allow) or r (reject)
            ('', 'meta', 'GET', 'a'),                       # Allow GET to anybody without auth
            ('', 'oauth', '', 'a'),                         # Allow any method to anybody without auth
            ('owner', 'callbacks/subscriptions', 'POST', 'a'),   # Allow owners on subscriptions
            ('', 'callbacks', '', 'a'),                     # Allow anybody callbacks witout auth
            ('creator', 'www', '', 'a'),                    # Allow only creator access to /www
            ('creator', 'properties', '', 'a'),             # Allow creator access to /properties
            ('associate', 'properties', 'GET', 'a'),        # Allow GET only to associate
            ('friend', 'properties', '', 'a'),              # Allow friend/partner/admin all
            ('partner', 'properties', '', 'a'),
            ('admin', 'properties', '', 'a'),
            ('creator', 'resources', '', 'a'),
            ('friend', 'resources', '', 'a'),               # Allow friend/partner/admin all
            ('partner', 'resources', '', 'a'),
            ('admin', 'resources', '', 'a'),
            ('', 'trust/<type>', 'POST', 'a'),              # Allow unauthenticated POST
            ('owner', 'trust/<type>/<id>', '', 'a'),        # Allow trust peer full access
            ('creator', 'trust', '', 'a'),                  # Allow access to all to
            ('trustee', 'trust', '', 'a'),                  # creator/trustee/admin
            ('admin', 'trust', '', 'a'),
            ('owner', 'subscriptions', '', 'a'),             # Owner can create++ own subscriptions
            ('creator', 'subscriptions', '', 'a'),           # Creator can do everything
            ('trustee', 'subscriptions', '', 'a'),           # Trustee can do everything
            ('creator', '/', '', 'a'),                       # Root access for actor
            ('trustee', '/', '', 'a'),
            ('admin', '/', '', 'a'),
        ]
        #########
        # Only touch the below if you know what you are doing
        #########
        logging.getLogger().handlers[0].setLevel(self.logLevel)  # Hack to get access to GAE logger
        self.root = self.proto + self.fqdn + "/"            # root URI used to identity actor externally
        self.auth_realm = self.fqdn                         # Authentication realm used in Basic auth

    def newUUID(self, seed):
        return uuid.uuid5(uuid.NAMESPACE_URL, seed).get_hex()

    def newToken(self, length=40):
        return binascii.hexlify(os.urandom(int(length // 2)))
