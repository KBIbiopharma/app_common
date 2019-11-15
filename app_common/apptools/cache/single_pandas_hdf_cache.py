import logging
from os.path import isfile, join
import os
import pandas as pd

from traits.api import Str

from .hdf_cache import HDF5IndexedCache

logger = logging.getLogger(__name__)

DEFAULT_HDF_DATA_KEY = "/data"


class HDF5SinglePandasCache(HDF5IndexedCache):
    """ Cache pandas objects (one per key), each key alone in an HDF5 file.

    In this cache, each key can be mapped to only 1 pandas object (Series or
    DataFrame), which is stored alone in any file at a fixed node: the mapping
    to the relative file path is controlled by the key_to_filepath_converter
    attribute.
    Note: Since there is only 1 DF per file, the node name is constant and
    isn't looked up using the :attr:`key_to_file_node_converter`.

    To conserve memory, no Pandas object is stored in memory: in memory is only
    the index dataframe, storing the path of the stored value, as well as the
    key's metadata.
    """
    #: Since there is only 1 DF per file, the node name constant:
    data_file_key = Str(DEFAULT_HDF_DATA_KEY)

    def get_value(self, key):
        """ Retrieve value corresponding to key.
        """
        h5store = self._get_file_handle(key)
        return h5store[self.data_file_key]

    # Private interface -------------------------------------------------------

    def _write_value(self, key, value, where, node_name=""):
        """ Implement adding a new entry in the cache.

        Parameters
        ----------
        key : str
            Name/key of the new entry.

        value : pd.DataFrame
            Data mapped to the provided key to store in the cache.

        where : str
            HDF group to write the value to.

        node_name : str, optional
            Unused.
        """
        h5store = self._get_file_handle(key)
        value.to_hdf(h5store, where)

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

        h5store = pd.HDFStore(filepath, mode="a", complib=self.complib,
                              complevel=self.complevel)
        self.open_files[filepath] = h5store
        return h5store

    def _prepare_node_path(self, key):
        """ Prepare target node for key setting.

        Current implementation stored 1 DF per file, so they can all use the
        same file node.
        """
        return self.data_file_key, self.data_file_key, None

    def _do_delete(self, keys=None):
        """ Delete all or some HDF5 files in the cache's url.
        """
        if keys:
            to_remove = self._data_container.loc[keys,
                                                 self.filepath_index_col]
            self._data_container = self._data_container.drop(keys)
            for relpath in to_remove:
                path = join(self.url, relpath)
                try:
                    if path in self.open_files:
                        self.open_files[path].close()
                    os.remove(path)
                except Exception as e:
                    msg = "Failed to delete file {}. Error was {}.".format(
                        path, e)
                    logger.error(msg)
        else:
            self._do_delete_all()
