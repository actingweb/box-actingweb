from google.appengine.ext import ndb

__all__ = [
    'Actor',
    'Property',
    'Trust',
    'Subscription',
]


class Actor(ndb.Model):
    id = ndb.StringProperty(required=True)
    creator = ndb.StringProperty()
    passphrase = ndb.StringProperty()


class Property(ndb.Model):
    id = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    value = ndb.TextProperty()


class Trust(ndb.Model):
    id = ndb.StringProperty(required=True)
    peerid = ndb.StringProperty(required=True)
    baseuri = ndb.StringProperty(required=True)
    type = ndb.StringProperty(required=True)
    relationship = ndb.StringProperty(required=True)
    secret = ndb.StringProperty(required=True)
    desc = ndb.TextProperty()
    approved = ndb.BooleanProperty()
    peer_approved = ndb.BooleanProperty()
    verified = ndb.BooleanProperty()
    verificationToken = ndb.StringProperty()


class Subscription(ndb.Model):
    id = ndb.StringProperty(required=True)
    peerid = ndb.StringProperty(required=True)
    subid = ndb.StringProperty(required=True)
    granularity = ndb.StringProperty()
    target = ndb.StringProperty()
    subtarget = ndb.StringProperty()
    seqnr = ndb.IntegerProperty(default=1)
    callback = ndb.BooleanProperty()


class SubscriptionDiff(ndb.Model):
    id = ndb.StringProperty(required=True)
    subid = ndb.StringProperty(required=True)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    diff = ndb.TextProperty()
    seqnr = ndb.IntegerProperty()
