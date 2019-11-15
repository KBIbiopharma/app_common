""" Interfaces for persistence of Traits objects
"""

from traits.api import Interface


class IWriter(Interface):
    """ Interface to store any Traits object to some storage.
    """
    def save(self, object_to_save, target_storage):
        """ Store an object to some target_storage.
        """


class IReader(Interface):
    """ Interface to read any Traits object from some storage.
    """
    def load(self, target_storage):
        """ Load an object from some target_storage.
        """
