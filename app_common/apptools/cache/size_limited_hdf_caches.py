import logging

from traits.api import Enum, HasStrictTraits, Int, List, Str

from .timestamped_hdf_caches import TimestampedSingleArrayCache, \
    TimestampedSinglePandasCache

logger = logging.getLogger(__name__)


class SizeLimitedCacheMixin(HasStrictTraits):
    """ Simple mixin class to support limiting cache sizes.

    Currently only supporting measuring the size of the cache by the number of
    key-value pairs it contains.

    TODO: add support for controlling the memory footprint of the cache
    rather than the number.
    """
    #: Max number of entries in the cache
    num_key_limit = Int

    #: Index column to use to select the oldest entry in the cache
    oldest_by = Enum(values="age_criteria")

    #: Possible index columns to use to select the oldest entry in the cache
    age_criteria = List

    def __init__(self, **traits):
        super(SizeLimitedCacheMixin, self).__init__(**traits)
        if self.num_key_limit <= 0:
            msg = "No max number of keys was specified. If no limit is " \
                  "needed, it is recommended to use a regular HDF " \
                  "implementation, or a regular timestamped implementation."
            logger.warning(msg)

    def initialize(self):
        super(SizeLimitedCacheMixin, self).initialize()

        if self.created_index_col in self._data_container:
            # Make sure the index is sorted by creation date, to speed up key
            # removal when based on creation dates:
            self._data_container = self._data_container.sort_values(
                by=self.created_index_col)

    # Private interface -------------------------------------------------------

    def _is_removal_needed(self):
        """ Returns the number of keys needed to be removed.
        """
        removal_needed = 0
        if self.num_key_limit:
            num_keys = len(self._data_container)
            cache_at_capacity = num_keys >= self.num_key_limit
            if cache_at_capacity:
                # There could be more than 1 key to remove if num_key_limit has
                # been changed:
                removal_needed = num_keys - self.num_key_limit + 1

        return removal_needed

    def _remove_oldest_keys(self, num_keys=1, oldest_by=None):
        """ Remove N oldest keys, sorting their age by a specific index column.

        Notes
        -----
        This assumes that the index is constantly sorted by creation date!
        """
        if oldest_by is None:
            oldest_by = self.oldest_by

        if oldest_by == self.last_used_index_col:
            sorted_index = self._data_container.sort_values(by=oldest_by)
        else:
            # sorted by self.created_index_col, which is the sorting by default
            sorted_index = self._data_container

        oldest_keys = sorted_index.index[:num_keys].tolist()

        msg = "Size limit reached: removing keys from cache: {}"
        logger.info(msg.format(oldest_keys))
        self.invalidate(keys=oldest_keys, skip_confirm=True)

    # Traits initialization methods -------------------------------------------

    def _age_criteria_default(self):
        return [self.last_used_index_col, self.created_index_col]


class SizeLimitedHDFSinglePandasCache(SizeLimitedCacheMixin,
                                      TimestampedSinglePandasCache):
    """ Cache mapping keys to single dataframes, which records access times and
    is limited in size.

    The maximum size is currently only set as a number of key-value pairs
    stored as memory footprint is complex and time-consuming to compute.

    Notes
    -----
    Make sure that for the timestamp_fmt attribute, you pick something where
    the string sorting matches the time sorting, so the oldest cache entry can
    be found by sorting by the created and last_used columns.
    """
    #: Format to store the datetime objects. Must be precise so age is accurate
    timestamp_fmt = Str("%Y/%m/%d %H:%M:%S:%f")

    def set_value(self, key, value, metadata=None, overwrite=False):
        num_keys_to_remove = self._is_removal_needed()
        if num_keys_to_remove:
            self._remove_oldest_keys(num_keys=num_keys_to_remove)

        super(SizeLimitedHDFSinglePandasCache, self).set_value(
            key, value, metadata=metadata, overwrite=overwrite)


class SizeLimitedHDFSingleArrayCache(SizeLimitedCacheMixin,
                                     TimestampedSingleArrayCache):
    """ Cache mapping keys to single arrays, which records access times and is
    limited in size.

    The maximum size is currently only set as a number of key-value pairs
    stored as memory footprint is complex and time-consuming to compute. It
    uses timestamping to measure which keys haven't been used most recently
    (read or write).

    Notes
    -----
    Make sure that for the timestamp_fmt attribute, you pick something where
    the string sorting matches the time sorting, so the oldest cache entry can
    be found by sorting by the created and last_used columns.
    """
    #: Format to store the datetime objects. Must be precise so age is accurate
    timestamp_fmt = Str("%Y/%m/%d %H:%M:%S:%f")

    def set_value(self, key, value, metadata=None, overwrite=False):
        num_keys_to_remove = self._is_removal_needed()
        if num_keys_to_remove:
            self._remove_oldest_keys(num_keys=num_keys_to_remove)

        super(SizeLimitedHDFSingleArrayCache, self).set_value(
            key, value, metadata=metadata, overwrite=overwrite)
