import logging
from os.path import abspath, isdir, join, split
import os
import numpy as np
from shutil import rmtree

from traits.api import Bool, Callable, Int, Str, Dict

from .base_cache import InMemoryCache

logger = logging.getLogger(__name__)

DEFAULT_HDF_DATA_KEY = "/data"

DEFAULT_COMP_LIB = "blosc"

DEFAULT_COMP_LEVEL = 9


class KeyFormatError(ValueError):
    """ Error raised when the key has a format incompatible with one of the
    cache converters: key -> filepath, ...
    """
    pass


class HDF5BaseCache(InMemoryCache):
    #: Folder containing the files the datasets are stored in
    url = Str

    #: Open HDF5 files
    open_files = Dict

    #: Compression library to use when storing in HDF5
    complib = Str(DEFAULT_COMP_LIB)

    #: Compression level to use when storing in HDF5
    complevel = Int(DEFAULT_COMP_LEVEL)

    #: Transform key to file path to store in, relative to url
    key_to_filepath_converter = Callable

    #: Transform key to HDF node path to store under (result must start by '/')
    key_to_file_node_converter = Callable

    #: Allow metadata to be modified?
    allow_metadata_modif = Bool(True)

    def initialize(self):
        """ Initialize directories if there is a URL and set cache flags.

        Set flags are changed and initialized. Also creates :attr:`url` folder
        if :attr:`auto_initialize` is `True`.
        """
        if self.url:
            if self.auto_initialize and not isdir(self.url):
                os.makedirs(self.url)

        super(HDF5BaseCache, self).initialize()

    def get_value(self, key):
        """ Retrieve value corresponding to key from file.
        """
        node = self._get_node(key, make_file=False)
        return np.array(node)

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
        if key in self:
            if overwrite:
                self.invalidate(keys=[key], skip_confirm=True)
            else:
                msg = "Key {} already in cache. Use `invalidate` method, or " \
                      "set overwrite to True.".format(key)
                logger.exception(msg)
                raise ValueError(msg)

        node_path, where, node_name = self._prepare_node_path(key)
        self._write_value(key, value, where, node_name)
        if metadata:
            self._set_metadata(key, **metadata)
        self.changed = True

    def close(self):
        self._close_hdf5_files()
        super(HDF5BaseCache, self).close()

    def set_metadata(self, key, **metadata):
        """ Set the metadata stored for a given key to a new value.

        Parameters
        ----------
        key : str
            Key to look up the metadata for.

        **metadata : dict
            Names and values of the metadata to add.
        """
        if not self.allow_metadata_modif:
            msg = "Not allowed to change metadata after their creation!"
            logger.exception(msg)
            raise ValueError(msg)

        self._set_metadata(key, **metadata)

    # Private interface -------------------------------------------------------

    def __init__(self, **traits):
        super(HDF5BaseCache, self).__init__(**traits)
        self.url = abspath(self.url)

    def __del__(self):
        """ Close open hdf5 file handles if user forgot to call :meth:`close`.
        """
        self._close_hdf5_files()

    def _close_hdf5_files(self):
        """ Close open hdf5 files.
        """
        for key in list(self.open_files.keys()):
            h5file = self.open_files.pop(key)
            h5file.close()

    def _do_delete_all(self):
        """ Delete the folder of HDF5 files.
        """
        self._close_hdf5_files()
        rmtree(self.url)
        os.makedirs(self.url)

    def _get_node(self, key, make_file=True, classname=None):
        """ Return HDF5 node
        """
        try:
            h5_file = self._get_file_handle(key, make_file=make_file)
            node_key = self.key_to_file_node_converter(key)
            node = h5_file.get_node(node_key, classname=classname)
        except Exception as e:
            msg = "Could not retrieve node for key: {}.\n " \
                  "Error was {}".format(key, e)
            logger.exception(msg)
            raise KeyError(msg)
        return node

    def _prepare_filepath(self, key, make_dir=True):
        """ Prepare target path for key setting.
        """
        try:
            relpath = self.key_to_filepath_converter(key)
        except Exception as e:
            msg = "Failed to parse the file path from the key {}. Check the" \
                  " key name and the cache converters. Error was {}"
            msg = msg.format(key, e)
            logger.exception(msg)
            raise KeyFormatError(msg)
        else:
            filepath = join(self.url, relpath)
            directory, filename = split(filepath)
            if not isdir(directory) and make_dir:
                os.makedirs(directory)

        return relpath, filepath

    # Traits initialization methods -------------------------------------------

    def _key_to_filepath_converter_default(self):
        """ All values stored on same node: expects keys to be different paths.
        """
        return lambda key: key + ".h5"

    def _key_to_file_node_converter_default(self):
        """ Default: values stored on same node: requires different file paths.
        """
        return lambda x: DEFAULT_HDF_DATA_KEY
