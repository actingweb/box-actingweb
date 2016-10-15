#!/usr/bin/env python
import webapp2
import logging
import time
import json
from actingweb import actor
from actingweb import oauth
from actingweb import config

__all__ = [
    'check_on_oauth_success',
]


def on_bot_post(req, auth, path):
    """Called on POSTs to /bot.
    
    auth will be initialised with the configured bot token to do
    oauth-authorized API calls.
    However, there will not be any actor iniatialised.
    """

    # Safety valve to make sure we don't do anything if bot is not
    # configured.
    Config = config.config()
    if not Config.bot['token'] or len(Config.bot['token']) == 0:
        return False

    #try:
    #     body = json.loads(req.request.body.decode('utf-8', 'ignore'))
    #     logging.debug('Bot callback: ' + req.request.body.decode('utf-8', 'ignore'))
    #except:
    #     return 405
    #
    # This is how actor can be initialised if the bot request
    # contains a value that has been stored as an actor property.
    # This value must be a primary key for the external oauth identity
    # that the actor is representing. 
    # Here, oauthId (from oauth service) has earlier been stored as a property
    #myself = actor.actor()
    #myself.get_from_property(name='oauthId', value=<PROPERTY-VALUE>)
    #if myself.id:
    #    logging.debug('Found actor(' + myself.id + ')')
    #
    # If we havent''
    #if not myself.id:
    #    myself.create(url=Config.root, creator= <EMAIL>,
    #                    passphrase=Config.newToken())
        #Now store the oauthId propery
    #    myself.setProperty('oauthId', <ID-VALUE>)
        # Send comfirmation message that actor has been created
    #    return True
    # Do something 
    return True
