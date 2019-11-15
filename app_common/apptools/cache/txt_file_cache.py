import logging
from os.path import abspath, isfile, splitext
import json

from .base_cache import InMemoryCache

logger = logging.getLogger(__name__)

CACHE_FILE_READERS = {".json": json.load}

CACHE_FILE_WRITERS = {".json": json.dump}


class SingleTxtFileDataCache(InMemoryCache):
    """ Cache object to store in local file data that doesn't change over time.

    Simplest implementation storing the data in a dictionary, and storing the
    content in a json file.

    FIXME: this implementation isn't very efficient when one wants to just
    append a small number of new entries, since it can't just append entries to
    the end of a json, so it has to load the index from file, add and save back
    to file.
    We should explore a csv based implementation, or something similar,
    where we can append in the file without having to load it all in memory.
    """
    def __init__(self, **traits):
        super(SingleTxtFileDataCache, self).__init__(**traits)
        self.url = abspath(self.url)

    def initialize(self):
        if self.url:
            self._load_data()
        super(SingleTxtFileDataCache, self).initialize()

    def close(self):
        if self.changed:
            self._save_data()
        super(SingleTxtFileDataCache, self).close()

    # Private interface -------------------------------------------------------

    def _load_data(self):
        if not isfile(self.url):
            if self.auto_initialize:
                self._data_container = {}
                return
            else:
                msg = "Cache url '{}' doesn't exist. Make sure it exists, or" \
                      " create the cache object with auto_initialize to True" \
                      " to create it.".format(self.url)
                logger.exception(msg)
                raise ValueError(msg)

        data_file_type = splitext(self.url)[1]
        try:
            cache_reader = CACHE_FILE_READERS[data_file_type]
        except KeyError as e:
            msg = "No reader provided for data file of type {}. Error was {}"
            msg = msg.format(data_file_type, e)
            raise ValueError(msg)

        with open(self.url, "r") as f:
            self._data_container = cache_reader(f)

    def _save_data(self):
        cache_writer = CACHE_FILE_WRITERS[splitext(self.url)[1]]
        with open(self.url, "w") as f:
            cache_writer(self._data_container, f)

    def _do_delete(self, keys=None):
        if keys is None:
            self._data_container.clear()
            # Save an emtpy dictionary to the text file:
            self._save_data()
        else:
            for key in keys:
                self._data_container.pop(key)
