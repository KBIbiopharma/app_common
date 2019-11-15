from datetime import datetime

from traits.api import HasStrictTraits, Str

from .single_array_hdf_cache import HDF5SingleArrayCache
from .single_pandas_hdf_cache import HDF5SinglePandasCache

LAST_USED_INDEX_COL = "last used"

CREATED_INDEX_COL = "created"

DEFAULT_TS_FMT = "%Y/%m/%d"


def generate_now_str(fmt):
    """ Returns a string version of 'now'."""
    return datetime.now().strftime(fmt)


class TimestampedCacheMixin(HasStrictTraits):
    """ Set of attributes to support recording timestamps for cache queries.
    """
    #: Format to store the datetime objects.
    timestamp_fmt = Str(DEFAULT_TS_FMT)

    #: Name of the index column to store the date(time) of key creation
    created_index_col = Str(CREATED_INDEX_COL)

    #: Name of the index column to store the date(time) of last key lookup
    last_used_index_col = Str(LAST_USED_INDEX_COL)


class TimestampedSingleArrayCache(TimestampedCacheMixin, HDF5SingleArrayCache):
    """ Timestamped version of the Array cache.

    The timestamp of every get_value and the set_value are recorded in the
    metadata under the columns named last_used_index_col and created_index_col
    respectively. Timestamps are stored as strings to simplify storage, and
    offer control over how granular we want it to be.
    """
    def get_value(self, key, **kwargs):
        value = super(TimestampedSingleArrayCache, self).get_value(key)
        now = generate_now_str(self.timestamp_fmt)
        self._set_metadata(key, **{self.last_used_index_col: now})
        return value

    def set_value(self, key, value, **kwargs):
        super(TimestampedSingleArrayCache, self).set_value(key, value,
                                                           **kwargs)
        now = generate_now_str(self.timestamp_fmt)
        metadata = {self.created_index_col: now,
                    self.last_used_index_col: now}
        self._set_metadata(key, **metadata)


class TimestampedSinglePandasCache(TimestampedCacheMixin,
                                   HDF5SinglePandasCache):
    """ Timestamped version of the Pandas cache.

    The timestamp of every get_value and the set_value are recorded in the
    metadata under the columns named last_used_index_col and created_index_col
    respectively. Timestamps are stored as strings to simplify storage, and
    offer control over how granular we want it to be.
    """
    def get_value(self, key, **kwargs):
        value = super(TimestampedSinglePandasCache, self).get_value(key)
        now = generate_now_str(self.timestamp_fmt)
        self._set_metadata(key, **{self.last_used_index_col: now})
        return value

    def set_value(self, key, value, metadata=None, overwrite=False):
        """ Add a new entry in the cache.

        Parameters
        ----------
        key : str
            Name/key of the new entry.

        value : any
            Data mapped to the provided key to store in the cache.

        metadata : dict
            Dictionary of metadata about the value being stored.

        overwrite : bool
            Overwrite value if the key already exists.
        """
        super(TimestampedSinglePandasCache, self).set_value(
            key, value, metadata=metadata, overwrite=overwrite
        )
        now = generate_now_str(self.timestamp_fmt)
        metadata = {self.created_index_col: now,
                    self.last_used_index_col: now}
        self._set_metadata(key, **metadata)
