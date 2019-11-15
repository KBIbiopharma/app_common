import logging
import tables as tb
from os.path import isfile

from traits.api import Str

from .hdf_cache import HDF5IndexedCache, HDF5NoIndexCache
from .base_hdf_cache import KeyFormatError

logger = logging.getLogger(__name__)


class HDF5SingleArrayNoIndexCache(HDF5NoIndexCache):
    """Cache array objects, with multiple keys in compressed HDF5 files.

    In this cache, each key can be mapped to only 1 array object, which can be
    stored in any file at any node: the mapping to these 2 properties is
    controlled by the key_to_filepath_converter and key_to_file_node_converter
    attributes.

    To conserve memory, no array is stored in memory.

    Similar to `HDF5SingleArrayCache`, but does not contain an index file to
    conserve memory for caches with millions+ of arrays.
    """
    array_title_fmt = Str("Value for {key}")

    # Private interface -------------------------------------------------------

    def _write_value(self, key, value, where, node_name=""):
        """ Implement adding a new entry in the cache.

        Parameters
        ----------
        key : str
            Name/key of the new entry.

        value : np.ndarray
            Data mapped to the provided key to store in the cache.
        """
        h5file = self._get_file_handle(key)
        h5_filters = tb.Filters(complib=self.complib,
                                complevel=self.complevel)
        h5file.create_carray(where, node_name, obj=value,
                             title=self.array_title_fmt.format(key=key),
                             filters=h5_filters, createparents=True)

    def _get_file_handle(self, key, make_file=True):
        """ Return HDF5 open file handle (mode="a").
        """
        _, filepath = self._prepare_filepath(key, make_dir=make_file)
        if filepath in self.open_files:
            return self.open_files[filepath]
        if not isfile(filepath) and not make_file:
            msg = "File does not exist for key: {}. You can make_file to " \
                  "True when calling _get_file_handle to create this " \
                  "file.".format(key)
            logger.exception(msg)
            raise KeyError(msg)

        h5file = tb.open_file(filepath, mode="a")
        self.open_files[filepath] = h5file
        return h5file

    def _prepare_node_path(self, key):
        """ Prepare target node for key setting.
        """
        try:
            node_path = self.key_to_file_node_converter(key)
        except Exception as e:
            msg = "Failed to parse the file path from the key {}. Check the " \
                  "key name and the cache converters. Error was {}"
            msg = msg.format(key, e)
            logger.exception(msg)
            raise KeyFormatError(msg)
        else:
            if not node_path.startswith("/"):
                msg = "key_to_file_node_converter should return a node path " \
                      "that starts with /, but {} was the node_path computed" \
                      " from the key {}".format(node_path, key)
                logger.exception(msg)
                raise ValueError(msg)

            # Split the node path on the group and the leaf node name:
            elements = node_path.split("/")
            node_name = elements[-1]
            # Make sure where starts with a '/' or it will be ignored:
            where = "/"
            if len(elements) > 2:
                # There is/are group(s) to place the array in.
                # 1:-1 to remove the empty string at the beginning of the path
                # and the leaf name at the end
                where += "/".join(elements[1:-1])

        return node_path, where, node_name

    def _do_delete(self, keys=None):
        """ Delete all or some HDF5 file nodes in the cache's url.
        """
        if keys:
            to_remove = set(keys)

            for key in to_remove:
                node = self.key_to_file_node_converter(key)
                h5file = self._get_file_handle(key)
                h5file.remove_node(node)
        else:
            self._do_delete_all()


class HDF5SingleArrayCache(HDF5IndexedCache, HDF5SingleArrayNoIndexCache):
    """ Cache array objects, with multiple keys in compressed HDF5 files.

    In this cache, each key can be mapped to only 1 array object, which can be
    stored in any file at any node: the mapping to these 2 properties is
    controlled by the key_to_filepath_converter and key_to_file_node_converter
    attributes.

    To conserve memory, no array is stored in memory: in memory is only the
    index dataframe, storing the path and node of the stored value, as well as
    the key's metadata.
    """

    # Private interface -------------------------------------------------------

    def _do_delete(self, keys=None):
        """ Delete all or some HDF5 file nodes in the cache's url.
        """
        super(HDF5SingleArrayCache, self)._do_delete(keys=keys)
        if keys:
            # Remove from the index:
            self._data_container = self._data_container.drop(keys)
