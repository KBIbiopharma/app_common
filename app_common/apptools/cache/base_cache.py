import logging

from traits.api import Any, Bool, Dict, HasStrictTraits

from app_common.std_lib.sys_utils import command_line_confirmation

logger = logging.getLogger(__name__)


class BaseCache(HasStrictTraits):
    """ Base class to implement caching of data together with metadata.
    """
    #: Address/path/... to _load_index the cache from
    url = Any

    def initialize(self):
        """ Initializes the cache so it is ready to serve or receive values.
        """
        pass

    def close(self):
        """ Closes the cache so the obj can be destroyed w/out loosing changes.
        """
        pass

    def get_value(self, key):
        """ Returns the value stored for :arg:`key`.

        Raises
        ------
        KeyError
            If the key is not in the cache.
        """
        pass

    def get_metadata(self, key, metadata_list=None):
        """ Returns the metadata stored for :arg:`key` or None if no metadata.

        Parameters
        ----------
        key : str
            Key to look up the metadata for.

        metadata_list : list, optional
            List of metadata names to collect. Leave as None to get them all.

        Raises
        ------
        KeyError
            If the key is not in the cache.
        """
        pass

    def set_value(self, key, value, metadata=None, overwrite=False):
        """ Set a new key-value pair."""
        pass

    def __contains__(self, item):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def invalidate(self, keys=None, skip_confirm=False):
        """ Cache (or just a set of keys) deemed invalid: empty it/remove them.
        """
        pass

    def list_content(self, key_filter=None, metadata_filter=None):
        """ Returns the list of keys the cache contains.

        If filters are provided, only a subset of the keys are returned, which
        comply to the key_filter or whose metadata comply with the metadata
        filter.
        """
        pass


class InMemoryCache(BaseCache):
    """ Base class to implement caching of data in a dict list container.
    """
    #: Store keys and (value, metadata) in a in-memory dict
    _data_container = Dict

    #: Flag to record if the cache's key list was modified since initialized
    changed = Bool

    #: Flag that records if the initialize method has been called.
    initialized = Bool

    #: Whether to initialize on creation
    auto_initialize = Bool

    def __init__(self, **traits):
        super(InMemoryCache, self).__init__(**traits)
        if self.auto_initialize:
            self.initialize()

    def initialize(self):
        self.changed = False
        self.initialized = True

    def close(self):
        self.changed = False

    def get_value(self, key):
        return self._data_container[key][0]

    def get_metadata(self, key, metadata_list=None):
        """ Returns dict with metadata requested, assigned to a specific key.

        Parameters
        ----------
        key : str
            Key to look up the metadata for.

        metadata_list : list, optional
            List of metadata names to collect. Leave as None to get them all.
        """
        if metadata_list:
            return {metadata: self._data_container[key][1][metadata]
                    for metadata in metadata_list}
        else:
            return self._data_container[key][1]

    def set_value(self, key, value, metadata=None, overwrite=False):
        """ Set a new key-value pair.
        """
        if key in self._data_container and not overwrite:
            msg = "{} already present in the cache. Use `remove_keys()` " \
                  "first or set `overwrite` to `True`.".format(key)
            raise ValueError(msg)

        self._data_container[key] = (value, metadata)

    def list_content(self, key_filter=None, metadata_filter=None):
        """ List the content (keys) of the cache, optionally following filters.

        Parameters
        ----------
        key_filter : callable
            Function to call on each key to select a subset of keys: must
            return True if to be selected or False otherwise.

        metadata_filter : callable
            Function to call on the metadata of each key to select a subset of
            keys: must return True if to be selected or False otherwise.

        Returns
        -------
        iterable
            List/set of keys in the cache, optionally following the provided
            filters.
        """
        if key_filter is None and metadata_filter is None:
            return self._data_container.keys()

        if key_filter and not metadata_filter:
            return {key for key in self._data_container if key_filter(key)}

        if not key_filter and metadata_filter:
            return {key for key, value in self._data_container.items()
                    if metadata_filter(value[1])}

        if key_filter and metadata_filter:
            return {key for key, value in self._data_container.items()
                    if key_filter(key) and metadata_filter(value[1])}

    def invalidate(self, keys=None, skip_confirm=False):
        """ Confirm and clear the cache (in memory and on disk if any).
        """
        if not skip_confirm:
            msg = "Are you sure you want to clear the cache? (This " \
                  "operation CANNOT be undone) [y/N]"
            do_delete = command_line_confirmation(msg=msg, default_value="n")
        else:
            do_delete = True

        if do_delete:
            self._do_delete(keys=keys)

    # Private interface -------------------------------------------------------

    def __contains__(self, key):
        """ Support testing if a key is in the cache.
        """
        return key in self._data_container

    def __enter__(self):
        """ Support using the cache using the with statement.
        """
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Support using the cache using the with statement.
        """
        self.close()

    def _do_delete(self, keys=None):
        if keys is None:
            self._data_container.clear()
        else:
            for key in keys:
                self._data_container.pop(key)

    # Traits listener methods -------------------------------------------------

    def __data_container_items_changed(self):
        self.changed = True
