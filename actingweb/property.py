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

    def set(self, value):
        if self.dbprop:
            self.dbprop.value = value
        else:
            self.dbprop = db.Property(id=self.actor.id, name=self.name, value=value)
        self.dbprop.put(use_cache=False)

    def delete(self):
        if self.dbprop:
            self.dbprop.key.delete(use_cache=False)

    def __init__(self, actor, name):
        self.dbprop = None
        self.name = name
        self.value = None
        if actor.id:
            self.actor = actor
            self.get()
