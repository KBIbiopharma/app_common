import logging
from os.path import isdir, isfile, join
import os
import pandas as pd
import tables as tb

from traits.api import Instance, Str

from .base_hdf_cache import HDF5BaseCache

logger = logging.getLogger(__name__)

DEFAULT_HDF_INDEX_FNAME = "index.h5"

DEFAULT_HDF_INDEX_NODE = "index"

PATH_INDEX_COL = "path"

NODE_PATH_INDEX_COL = "node_path"


class HDF5NoIndexCache(HDF5BaseCache):
    """ Base cache class to compressed HDF5 files without a central index.

    Since there is no index, metadata are stored at the node level.

    Subclasses implement their own value storage, only metadata handling is
    done on HDF nodes. Being index-less, this implementation doesn't offer
    :meth:`list_content`.
    """
    def list_content(self, key_filter=None, metadata_filter=None):
        """ List cache content not implemented!

        Subclasses may implement a HDF5 and file traversal method, but
        optimization depends heavily on the anticipated file and node
        structure.
        """
        msg = 'list_content method not implemented in no index caches'
        logger.exception(msg)
        raise NotImplementedError(msg)

    def __contains__(self, key):
        """ Key contained if corresponding HDF5 node exists."""
        h5file = self._get_file_handle(key)
        node_key = self.key_to_file_node_converter(key)
        return node_key in h5file

    def get_metadata(self, key, metadata_list=None):
        """ Returns the metadata stored for a given key.

        Parameters
        ----------
        key : str
            Key to look up the metadata for.

        metadata_list : list
            list of metadata attributes to include

        Returns
        -------
        dict
            Dictionary where keys specify the metadata attribute, and value
            is the metadata attribute value.
        """
        h5file = self._get_file_handle(key)
        node_key = self.key_to_file_node_converter(key)
        try:
            node = h5file.get_node(node_key, classname='Leaf')
        except tb.NoSuchNodeError:
            msg = "Node for key {} does not exist".format(key)
            logger.exception(msg)
            raise KeyError(msg)
        else:
            try:
                metadata = node.attrs.metadata
            except AttributeError:
                metadata = {}

        if metadata_list:
            metadata = {key: metadata[key] for key in metadata_list}
        return metadata

    def _set_metadata(self, key, **metadata):
        """ Actual implementation of the setting of the metadata.
        """
        node = self._get_node(key, classname='Leaf')
        try:
            node_metadata = node.attrs.metadata
        except AttributeError:
            # No metadata stored on the node yet
            node.attrs.metadata = metadata
        else:
            for attr, value in metadata.items():
                node_metadata[attr] = value


class HDF5IndexedCache(HDF5BaseCache):
    """ Base class to cache objects in compressed HDF5 files.

    Subclasses implement their own value storage, but the index handling is
    done here: data is stored as a DataFrame, containing the file path and file
    node of the values, as well as any metadata corresponding to the key.

    FIXME: the set_value implementation is computationally inefficient because
    it appends 1 row at a time to the index DF. We should offer a
    _multi_do_set_value that optimizes adding many values at once.
    """
    #: Index dataframe mapping cache keys to their HDF path and metadata
    _data_container = Instance(pd.DataFrame)

    #: Name of the json file where the _data_container is serialized
    index_filename = Str(DEFAULT_HDF_INDEX_FNAME)

    #: Name of column in index DF to look up the value's relative file path
    filepath_index_col = Str(PATH_INDEX_COL)

    #: Index column containing array node name
    node_path_index_col = Str(NODE_PATH_INDEX_COL)

    def initialize(self):
        """ Initialize the index if there is a URL and set cache flags.

        Set flags are changed and initialized. Also creates :attr:`url` folder
        if :attr:`auto_initialize` is `True`.
        """
        super(HDF5IndexedCache, self).initialize()
        if self.url:
            self._load_index()

    def close(self):
        if self.changed:
            self._save_index()
        super(HDF5IndexedCache, self).close()

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
        if metadata_filter is not None:
            pass

        if key_filter is None:
            return self._data_container.index.tolist()
        else:
            return {key for key in self._data_container.index
                    if key_filter(key)}

    def get_metadata(self, key, metadata_list=None):
        """ Returns the metadata stored in the index for a given key.

        Parameters
        ----------
        key : str
            Key to look up the metadata for.

        metadata_list : list, optional
            List of metadata names to collect. Leave as None to get them all.
        """
        if not metadata_list:
            all_data = self._data_container.loc[key, :].to_dict()
            all_data.pop(self.filepath_index_col, None)
            all_data.pop(self.node_path_index_col, None)
            return all_data
        else:
            return self._data_container.loc[key, metadata_list].to_dict()

    def _set_metadata(self, key, **metadata):
        """ Set the metadata stored for a given key to a new value.

        By default, this is not permitted, and metadata should be set when
        creating the new entry (using :meth:`set_value`). Set
        :attr:`allow_metadata_modif` to `True` to allow.

        Parameters
        ----------
        key : str
            Key to look up the metadata for.

        **metadata : dict
            All metadata to set, mapping the metadata name to its value.
        """

        if key not in self._data_container.index:
            msg = "Unable to add/modify metadata for a key ({}) that " \
                  "doesn't exist.".format(key)
            logger.exception(msg)
            raise KeyError(msg)

        for name, value in metadata.items():
            self._data_container.loc[key, name] = value

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
        # Skip metadata: will be added below when updating the index:
        super(HDF5IndexedCache, self).set_value(key, value, metadata={},
                                                overwrite=overwrite)

        # Add relative file path and node path to the index:
        relpath, _ = self._prepare_filepath(key)
        node_path, _, _ = self._prepare_node_path(key)

        data = {self.filepath_index_col: relpath,
                self.node_path_index_col: node_path}
        if metadata:
            data.update(metadata)

        # df.append method would take in a dict for the row, but would convert
        # it to a series then a DF, then call pd.concat, so we are doing it
        # ourselves:
        # Also the special casing for len(self._data_container) == 0 is
        # required to avoid appending to an empty DF, which messes up the
        # dtypes (promotes int values to float columns)
        new_row = pd.DataFrame([pd.Series(data, name=key)])
        self._data_container = pd.concat([self._data_container, new_row])

    # Private interface -------------------------------------------------------

    def __contains__(self, item):
        """ Key contained if present in the index."""
        return item in self._data_container.index

    def _load_index(self):
        """ Load the index of the data contained in the cache.
        """
        if not isdir(self.url):
            msg = "Unable to find the cache folder at {}.".format(self.url)
            logger.exception(msg)
            raise ValueError(msg)

        index_file = join(self.url, self.index_filename)
        if not isfile(index_file):
            if not os.listdir(self.url):
                # New cache: no index to load
                self._set_index_as_empty()
            else:
                msg = "Unable to find the cache index in {}.".format(self.url)
                logger.exception(msg)
                raise ValueError(msg)
        else:
            self._data_container = pd.read_hdf(index_file,
                                               DEFAULT_HDF_INDEX_NODE)

    def _set_index_as_empty(self):
        self._data_container = pd.DataFrame([])

    def _save_index(self):
        """ Dump the index of the data contained to as json file.
        """
        path = join(self.url, self.index_filename)
        self._data_container.to_hdf(path, DEFAULT_HDF_INDEX_NODE)

    def _do_delete_all(self):
        """ Delete the folder of HDF5 files. Empty the index and save it too.
        """
        super(HDF5IndexedCache, self)._do_delete_all()
        # Clean the in-memory cache
        self._set_index_as_empty()
