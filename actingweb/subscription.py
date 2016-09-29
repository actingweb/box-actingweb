import actor
from db import db
import config
import datetime
import logging

__all__ = [
    'subscription',
]


class subscription():
    """Base class with core subscription methods (db-related)"""

    def get(self):
        """Retrieve subscription from db given pre-initialized variables """
        if self.peerid and self.subid:
            result = db.Subscription.query(db.Subscription.id == self.actor.id,
                                           db.Subscription.peerid == self.peerid,
                                           db.Subscription.subid == self.subid).get(use_cache=False)
            if result:
                self.subscription = result
                self.target = result.target
                self.subtarget = result.subtarget
                self.granularity = result.granularity
                self.seqnr = result.seqnr
                self.callback = result.callback

    def create(self, target=None, subtarget=None, granularity=None, seqnr=1):
        """Create new subscription and push it to db"""
        Config = config.config()
        if not self.peerid:
            return False
        if not target:
            target = ''
        if not subtarget:
            subtarget = ''
        if not granularity:
            granularity = ''
        self.target = target
        self.subtarget = subtarget
        self.granularity = granularity
        self.seqnr = seqnr
        if not self.subid:
            now = datetime.datetime.now()
            seed = Config.root + now.strftime("%Y%m%dT%H%M%S%f")
            self.subid = Config.newUUID(seed)
        elif self.subid and self.peerid and not self.subscription:
            self.get()
        if self.subscription:
            self.subscription.target = target
            self.subscription.subtarget = subtarget
            self.subscription.granularity = granularity
            self.subscription.seqnr = seqnr
            self.subscription.callback = self.callback
        else:
            self.subscription = db.Subscription(id=self.actor.id,
                                                peerid=self.peerid,
                                                subid=self.subid,
                                                target=target,
                                                subtarget=subtarget,
                                                granularity=granularity,
                                                seqnr=seqnr,
                                                callback=self.callback
                                                )
        self.subscription.put(use_cache=False)
        return True

    def delete(self):
        """Delete a subscription in db"""
        diffs = self.getDiffs()
        for diff in diffs:
            diff.key.delete()
        if self.subscription:
            self.subscription.key.delete(use_cache=False)
            return True
        return False

    def increaseSeq(self):
        if not self.subscription:
            self.get()
        if self.subscription:
            self.seqnr += 1
            self.subscription.seqnr = self.seqnr
            self.subscription.put(use_cache=False)
            return True
        return False

    def addDiff(self, blob=None):
        """Add a new diff for this subscription timestamped with now"""
        if not self.actor.id or not self.subid or not blob:
            return False
        diff = db.SubscriptionDiff(id=self.actor.id,
                                   subid=self.subid,
                                   diff=blob,
                                   seqnr=self.seqnr
                                   )
        diff.put(use_cache=False)
        if not self.increaseSeq():
            logging.error("Failed increasing sequence number for subscription " +
                          self.subid + " for peer " + self.peerid)
        return diff

    def getDiff(self, seqid=0):
        """Get one specific diff"""
        if seqid == 0:
            return None
        if not isinstance(seqid, int):
            return None
        return db.SubscriptionDiff.query(db.SubscriptionDiff.id == self.actor.id,
                                         db.SubscriptionDiff.subid == self.subid,
                                         db.SubscriptionDiff.seqnr == seqid).get(use_cache=False)

    def getDiffs(self):
        """Get all the diffs available for this subscription ordered by the timestamp, oldest first"""
        return db.SubscriptionDiff.query(db.SubscriptionDiff.id == self.actor.id,
                                         db.SubscriptionDiff.subid == self.subid).order(db.SubscriptionDiff.seqnr).fetch(use_cache=False)

    def clearDiff(self, seqid):
        """Clears one specific diff"""
        diff = self.getDiff(seqid)
        if diff:
            diff.key.delete(use_cache=False)
            return True
        return False

    def clearDiffs(self, seqnr=0):
        """Clear all diffs up to and including a seqnr"""
        diffs = self.getDiffs()
        for diff in diffs:
            if seqnr != 0 and diff.seqnr > seqnr:
                break
            diff.key.delete(use_cache=False)

    def __init__(self, actor=None, peerid=None, subid=None, callback=False):
        self.peerid = peerid
        self.subid = subid
        self.subscription = None
        self.callback = callback
        self.seqnr = 1
        self.target = None
        self.subtarget = None
        self.granularity = None
        if not actor:
            return False
        self.actor = actor
        if self.actor.id and self.peerid and self.subid:
            self.get()
