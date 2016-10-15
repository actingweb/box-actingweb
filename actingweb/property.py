import actor
from db import db
import datetime
import uuid

__all__ = [
    'property',
]


class property():

    def get(self):
        result = db.Property.query(db.Property.id == self.actor.id,
                                   db.Property.name == self.name).get(use_cache=False)
        if result:
            self.dbprop = result
            self.value = result.value
        else:
            self.dbprop = None
            self.value = None

    def get_from_property(self):
        """ Initialises a property based on the value of a property.

        Note that this is a costly operation as all properties of this type
        must be retrieved and processed as value is TextProperty and cannot
        be indexed.
        """
        results = db.Property.query(db.Property.name == self.name).fetch(use_cache=False)
        result = None
        for res in results:
            if res.value != self.value:
                continue
            result = res
            break
        if not result:
            self.value = None
            return None
        self.dbprop = result
        return result.id

    def set(self, value):
        if self.dbprop:
            self.dbprop.value = value
        else:
            self.dbprop = db.Property(id=self.actor.id, name=self.name, value=value)
        self.dbprop.put(use_cache=False)

    def delete(self):
        if self.dbprop:
            self.dbprop.key.delete(use_cache=False)

    def __init__(self, actor=None, name=None, value = None):
        self.dbprop = None
        self.name = name
        self.value = value
        self.actorId = None
        if not value and actor and actor.id:
            self.actor = actor
            self.get()
        else:
            self.actor = None
            self.actorId = self.get_from_property()
