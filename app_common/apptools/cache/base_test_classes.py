import os
from os.path import abspath, dirname, isdir, isfile, join
import shutil
import pandas as pd
import tables as tb
from time import sleep
from numpy.testing import assert_array_equal

from app_common.apptools.cache.hdf_cache import DEFAULT_HDF_INDEX_FNAME, \
    DEFAULT_HDF_INDEX_NODE, NODE_PATH_INDEX_COL, PATH_INDEX_COL
from app_common.apptools.cache.timestamped_hdf_caches import \
    CREATED_INDEX_COL, DEFAULT_TS_FMT, generate_now_str, LAST_USED_INDEX_COL

HERE = dirname(__file__)

# Node path will be inside this group:
DEFAULT_VALUE_GROUP = "Values"

TODAY = generate_now_str(DEFAULT_TS_FMT)


class BaseHDF5CacheFromScratch(object):
    """ Ability to create new caches from non-existent or empty folders.
    """
    def setUp(self):
        self.new_cache_path = "temp2"

    def tearDown(self):
        if isdir(self.new_cache_path):
            num_attempts = 3
            # If it fails, try again
            for i in range(num_attempts):
                try:
                    shutil.rmtree(self.new_cache_path)
                    break
                except Exception:
                    sleep(.2)
            else:
                raise

    def test_create_new_empty_cache(self):
        """ New cache can be created from empty existing folder.
        """
        url = self.new_cache_path
        os.makedirs(url)
        cache = self.cache_klass(url=url)
        self.assert_usable_cache(cache)

    def test_auto_initialize_creates_cache_folder(self):
        """ New cache can be created from empty non-existing folder with
        auto-initialize.
        """
        self.assertFalse(isdir(self.new_cache_path))
        cache = self.cache_klass(url=self.new_cache_path,
                                 auto_initialize=True)
        # Thanks to auto_initialize, no need for os.makedirs:
        self.assert_usable_cache(cache)

    def test_cache_with_subdirectories(self):
        """ If filepath contains non-existing folders, they will be created.
        """
        key = "dir/fname/node0"

        def path_converter(x):
            return join(*x.split("/")[:2]) + ".h5"

        def node_converter(x):
            return "/" + x.split("/")[-1]

        cache = self.cache_klass(
            url=self.new_cache_path, key_to_filepath_converter=path_converter,
            key_to_file_node_converter=node_converter, auto_initialize=True
        )
        self.assert_usable_cache(cache, key=key)
        subdir = join(self.new_cache_path, "dir")
        self.assertTrue(isdir(subdir))
        self.assertTrue(isfile(join(subdir, "fname.h5")))

    # Utilities ---------------------------------------------------------------

    def assert_usable_cache(self, cache, key="abc"):
        cache.initialize()
        self.assertEqual(cache.list_content(), [])
        cache.set_value(key, self.value)
        self.assertEqual(cache.list_content(), [key])
        self.assert_value_equal(cache.get_value(key), self.value)
        cache.close()
        cache.initialize()
        self.assertEqual(cache.list_content(), [key])
        self.assert_value_equal(cache.get_value(key), self.value)

        key2 = key + "2"
        cache.set_value(key2, self.value)
        self.assertEqual(cache.list_content(), [key, key2])
        self.assert_value_equal(cache.get_value(key2), self.value)


class BaseHDF5CacheFromScratchNoIndex(BaseHDF5CacheFromScratch):
    """ Ability for no index caches to create from non-existent or empty
    folders.
    """

    def assert_usable_cache(self, cache, key="abc"):
        cache.initialize()
        cache.set_value(key, self.value)
        self.assert_value_equal(cache.get_value(key), self.value)
        cache.close()
        cache.initialize()
        self.assert_value_equal(cache.get_value(key), self.value)

        key2 = key + "2"
        cache.set_value(key2, self.value)
        self.assert_value_equal(cache.get_value(key), self.value)
        self.assert_value_equal(cache.get_value(key2), self.value)


class BaseHDF5CacheNoIndex(object):
    """Test access of data to/from an existing no index cache.
    """
    @classmethod
    def setUpClass(cls):
        cls.cache_folder_name = "temp"
        cls.cache_path = abspath(join(HERE, "tests", cls.cache_folder_name))
        cls.cache_traits = {}

    def setUp(self):
        if isdir(self.cache_path):
            shutil.rmtree(self.cache_path)

        os.makedirs(self.cache_path)
        # Prepare value data and index data
        self.hdf_relpath = self.path_converter(self.key1)
        self.hdf_fpath = join(self.cache_path, self.hdf_relpath)
        self.hdf_node = self.node_converter(self.key1)

        # Create cache object
        self.cache = self.cache_klass(
            url=self.cache_path, key_to_filepath_converter=self.path_converter,
            key_to_file_node_converter=self.node_converter,
            **self.cache_traits
        )
        self.create_cache_content()

    def tearDown(self):
        self.cache.close()
        if isdir(self.cache_path):
            num_attempts = 3
            # If it fails, try again
            for i in range(num_attempts):
                try:
                    shutil.rmtree(self.cache_path)
                    break
                except Exception:
                    sleep(.2)

    def test_initialize(self):
        cache = self.cache_klass(url=self.cache_path)
        self.assertFalse(cache.initialized)
        cache.initialize()
        self.assertTrue(cache.initialized)
        cache.initialize()
        self.assertTrue(cache.initialized)

    def test_auto_initialize(self):
        cache = self.cache_klass(url=self.cache_path, auto_initialize=True)
        self.assertTrue(cache.initialized)
        cache.initialize()
        self.assertTrue(cache.initialized)

    def test_get_value(self):
        value = self.cache.get_value(self.key1)
        self.assert_value_equal(value, self.value)
        self.assert_key_in_cache(self.key1)

    def test_get_value_non_existent(self):
        with self.assertRaises(KeyError):
            self.cache.get_value("NON EXISTENT")

    def test_set_value(self):
        key = self.key1 + "2"
        self.assert_key_not_in_cache(key)
        self.cache.set_value(key, self.value)
        self.assert_key_in_cache(key)
        value = self.cache.get_value(key)
        self.assert_value_equal(value, self.value)

    def test_changed_flag(self):
        key = self.key1 + "2"
        self.assertFalse(self.cache.changed)
        self.cache.set_value(key, self.value)
        self.assertTrue(self.cache.changed)

    def test_set_metadata_create_allowed(self):
        self.cache.set_metadata(self.key1, foo=1)
        metadata = self.cache.get_metadata(self.key1)
        self.assertEqual(metadata["foo"], 1)

    def test_set_different_metadata_allowed(self):
        # Key1 and key2 have different metadata and that's not a problem:
        self.cache.set_metadata(self.key1, foo=1)
        self.cache.set_value(self.key2, self.value, metadata={"bar": 2})
        metadata = self.cache.get_metadata(self.key1)
        self.assertEqual(metadata["foo"], 1)
        metadata = self.cache.get_metadata(self.key2)
        self.assertEqual(metadata["bar"], 2)

    def test_set_metadata_and_modify_allowed(self):
        self.cache.set_value(self.key2, self.value, metadata={"foo": "bar"})
        all_metadata = self.cache.get_metadata(self.key2)
        self.assertEqual(all_metadata["foo"], "bar")

        self.cache.set_metadata(self.key2, foo=1)
        all_metadata = self.cache.get_metadata(self.key2)
        self.assertEqual(all_metadata["foo"], 1)

    def test_set_metadata_on_creation_despite_preventing_modif(self):
        self.cache.allow_metadata_modif = False
        self.cache.set_value(self.key2, self.value, metadata={"foo": 1})
        all_metadata = self.cache.get_metadata(self.key2)
        self.assertEqual(all_metadata["foo"], 1)

    def test_prevent_set_metadata_modify(self):
        self.cache.allow_metadata_modif = False
        self.cache.set_value(self.key2, self.value, metadata={"foo": "bar"})
        with self.assertRaises(ValueError):
            self.cache.set_metadata(self.key2, foo=1)

    def test_set_value_with_metadata(self):
        key = self.key1 + "2"
        self.cache.set_value(key, self.value, metadata={"attr1": "attr_val"})
        self.assert_key_in_cache(key)
        value = self.cache.get_value(key)
        self.assert_value_equal(value, self.value)
        metadata = self.cache.get_metadata(key)
        self.assertEqual(metadata, {"attr1": "attr_val"})

    def test_get_specific_metadata(self):
        key = self.key1 + "2"
        metadata = {"attr1": "attr_val",
                    "attr2": "attr_val2",
                    "attr3": "attr_val3"}
        self.cache.set_value(key, self.value, metadata=metadata)
        metadata = self.cache.get_metadata(key,
                                           metadata_list=["attr1", "attr2"])
        self.assertEqual(metadata, {"attr1": "attr_val", "attr2": "attr_val2"})

    def test_set_bad_value(self):
        key = self.key1 + "2"
        with self.assertRaises(Exception):
            # 1 is a bad value because not an array
            self.cache.set_value(key, 1)

    def test_set_value_twice(self):
        key = self.key1 + "2"
        self.assert_key_not_in_cache(key)
        self.cache.set_value(key, self.value)
        self.assert_key_in_cache(key)

        # Adding it a second time isn't allowed
        with self.assertRaises(ValueError):
            self.cache.set_value(key, self.value)

    def test_set_value_twice_with_overwrite(self):
        self.assert_key_in_cache(self.key1)
        self.cache.set_value(self.key1, self.value2, overwrite=True)
        val = self.cache.get_value(self.key1)
        self.assert_key_in_cache(self.key1)
        self.assert_value_equal(val, self.value2)

    def test_invalidate_cache(self):
        self.assert_key_in_cache(self.key1)
        self.cache.invalidate(skip_confirm=True)
        self.assert_key_not_in_cache(self.key1)

    def test_invalidate_cache_multi_keys(self):
        # Add a second key so 2 keys will be invalidated:
        key = self.key1 + "2"
        self.cache.set_value(key, self.value)

        self.assert_key_in_cache(key)
        self.assert_key_in_cache(self.key1)

        self.cache.invalidate(skip_confirm=True)
        self.assert_key_not_in_cache(key)
        self.assert_key_not_in_cache(self.key1)

    def test_invalidate_1_key_from_cache(self):
        # Add a second key to invalidate:
        key = self.key1 + "2"
        self.cache.set_value(key, self.value)

        self.cache.invalidate(keys=[key], skip_confirm=True)
        self.assert_key_not_in_cache(key)
        self.assert_key_in_cache(self.key1)

    # Helper methods ----------------------------------------------------------

    def assert_key_in_cache(self, key):
        self.assertIn(key, self.cache)
        expected_filepath = join(self.cache_path, self.path_converter(key))
        node = self.node_converter(key)
        array_stored = isfile(expected_filepath) and \
            node_in_hdf5(expected_filepath, node)
        self.assertTrue(array_stored)

    def assert_key_not_in_cache(self, key):
        self.assertNotIn(key, self.cache)
        expected_filepath = join(self.cache_path, self.path_converter(key))
        node = self.node_converter(key)
        if isfile(expected_filepath):
            self.assertFalse(node_in_hdf5(expected_filepath, node))

    def assert_value_equal(self, val1, val2):
        assert_array_equal(val1, val2)

    def create_cache_content(self):
        with tb.open_file(self.hdf_fpath, "a") as h5file:
            h5file.create_group("/", DEFAULT_VALUE_GROUP)
            h5_filter = tb.Filters(complib="blosc", complevel=9)
            h5file.create_carray("/" + DEFAULT_VALUE_GROUP,
                                 self.node_leaf_name,
                                 obj=self.value, filters=h5_filter)


class BaseHDF5Cache(BaseHDF5CacheNoIndex):
    """ Extends no index cache with additional tests of index functionality
    """
    @classmethod
    def setUpClass(cls):
        super(BaseHDF5Cache, cls).setUpClass()
        cls.index_file = join(cls.cache_path, DEFAULT_HDF_INDEX_FNAME)

    def setUp(self):
        super(BaseHDF5Cache, self).setUp()
        self.create_index_file()
        self.cache.initialize()

    # Test methods ------------------------------------------------------------

    def test_initialize_bad_fname(self):
        cache = self.cache_klass(url=self.cache_path,
                                 index_filename="NON-EXISTENT")
        with self.assertRaises(ValueError):
            cache.initialize()

    def test_list_content_all(self):
        # Add a second key
        key = self.key1 + "2"
        self.cache.set_value(key, self.value)
        self.assertEqual(set(self.cache.list_content()), {self.key1, key})

    def test_list_content_filter_keys(self):
        # Add a second key
        key = self.key1 + "2"
        self.cache.set_value(key, self.value)

        content = self.cache.list_content(key_filter=lambda x: x.endswith("2"))
        self.assertEqual(set(content), {key})

    def test_dont_write_index_on_close_if_unmodified(self):
        last_modified = os.path.getmtime(self.index_file)
        self.cache.close()
        self.assertEqual(last_modified, os.path.getmtime(self.index_file))

    def test_write_index_on_close_if_modified(self):
        self.cache.set_value(self.key2, self.value)
        self.cache.close()
        # Make sure the new value is stored in the index:
        index_df = self.load_index_file()
        self.assertIn(self.key2, index_df.index)

    def test_context_manager_set_value(self):
        traits = dict(key_to_filepath_converter=self.path_converter,
                      key_to_file_node_converter=self.node_converter)

        with self.cache_klass(url=self.cache_path, **traits) as cache:
            cache.set_value(self.key2, self.value)

        # Make sure the new value is stored in the index:
        index_df = self.load_index_file()
        self.assertIn(self.key2, index_df.index)

    def test_context_manager_get_value(self):
        last_modified = os.path.getmtime(self.index_file)
        traits = dict(key_to_filepath_converter=self.path_converter,
                      key_to_file_node_converter=self.node_converter)

        with self.cache_klass(url=self.cache_path, **traits) as cache:
            value = cache.get_value(self.key1)
            self.assert_value_equal(value, self.value)

        # Index file not rewritten:
        self.assertEqual(last_modified, os.path.getmtime(self.index_file))

    # Helper methods ----------------------------------------------------------

    def create_index_file(self):
        default_data = pd.DataFrame({PATH_INDEX_COL: [self.hdf_relpath],
                                     NODE_PATH_INDEX_COL: [self.hdf_node]},
                                    index=[self.key1])
        default_data.to_hdf(self.index_file, DEFAULT_HDF_INDEX_NODE)

    def load_index_file(self):
        return pd.read_hdf(self.index_file, DEFAULT_HDF_INDEX_NODE)


class BaseTimestampedCacheMetadataTests(BaseHDF5Cache):
    """ Additional tests for timestamped implementations.
    """
    def test_set_value_with_metadata(self):
        key = self.key1 + "2"
        self.cache.set_value(key, self.value, metadata={"attr1": "attr_val"})
        self.assert_key_in_cache(key)
        value = self.cache.get_value(key)
        self.assert_value_equal(value, self.value)
        metadata = self.cache.get_metadata(key)
        # Created and last used metadata automatically added:
        self.assertEqual(metadata, {"attr1": "attr_val",
                                    CREATED_INDEX_COL: TODAY,
                                    LAST_USED_INDEX_COL: TODAY})

    def test_set_value_with_metadata_last_used_by_set_value(self):
        # Above test calls get_value before checking all metadata. This skips
        # the get_value to make sure set_value sets the last_used metadata too
        key = self.key1 + "2"
        self.cache.set_value(key, self.value, metadata={"attr1": "attr_val"})
        self.assert_key_in_cache(key)
        metadata = self.cache.get_metadata(key)
        self.assertEqual(metadata, {"attr1": "attr_val",
                                    CREATED_INDEX_COL: TODAY,
                                    LAST_USED_INDEX_COL: TODAY})

    def test_set_metadata_create_fail_non_existent_key(self):
        with self.assertRaises(KeyError):
            self.cache.set_metadata("NONEXISTENT", new_metadata=1)

    def test_set_metadata_create(self):
        self.cache.set_metadata(self.key1, new_metadata=1)
        data = self.cache.get_metadata(self.key1,
                                       metadata_list=["new_metadata"])
        self.assertEqual(data, {"new_metadata": 1})

    def test_set_metadata_modify(self):
        self.cache.set_value(self.key2, self.value, metadata={"foo": "bar"})
        self.cache.set_metadata(self.key2, foo=1)
        data = self.cache.get_metadata(self.key2, metadata_list=["foo"])
        self.assertEqual(data, {"foo": 1})

    def create_index_file(self):
        fmt = self.cache_traits.get("timestamp_fmt", DEFAULT_TS_FMT)
        now = generate_now_str(fmt)
        default_data = pd.DataFrame({PATH_INDEX_COL: [self.hdf_fpath],
                                     NODE_PATH_INDEX_COL: [self.hdf_node],
                                     CREATED_INDEX_COL: [now],
                                     LAST_USED_INDEX_COL: [now]},
                                    index=[self.key1])
        default_data.to_hdf(self.index_file, DEFAULT_HDF_INDEX_NODE)


class BaseSizeLimitedCacheMetadataTests(BaseTimestampedCacheMetadataTests):
    """ Additional tests for timestamped size limited implementations.
    """
    def test_set_value_with_metadata(self):
        key = self.key1 + "2"
        self.cache.set_value(key, self.value, metadata={"attr1": "attr_val"})
        self.assert_key_in_cache(key)
        value = self.cache.get_value(key)
        self.assert_value_equal(value, self.value)
        metadata = self.cache.get_metadata(key)
        # Created and last used metadata automatically added. In this
        # implementation, microsecond timestamp needed, so only check the keys.
        self.assertEqual(set(metadata.keys()),
                         {"attr1", CREATED_INDEX_COL, LAST_USED_INDEX_COL})

    def test_set_value_with_metadata_last_used_by_set_value(self):
        # Above test calls get_value before checking all metadata. This skips
        # the get_value to make sure set_value sets the last_used metadata too
        key = self.key1 + "2"
        self.cache.set_value(key, self.value, metadata={"attr1": "attr_val"})
        self.assert_key_in_cache(key)
        metadata = self.cache.get_metadata(key)
        # In this implementation, microsecond timestamp needed, so only check
        # the keys:
        self.assertEqual(set(metadata.keys()),
                         {"attr1", CREATED_INDEX_COL, LAST_USED_INDEX_COL})

    def test_create_cache_with_num_limit(self):
        cache = self.cache_klass(
            url=self.cache_path, key_to_filepath_converter=self.path_converter,
            key_to_file_node_converter=self.node_converter,
            num_key_limit=2
        )
        cache.initialize()
        cache.set_value(self.key2, self.value)
        self.assert_value_equal(cache.get_value(self.key1), self.value)
        self.assert_value_equal(cache.get_value(self.key2), self.value)

    def test_set_cache_num_limit_after_creation(self):
        cache = self.cache_klass(
            url=self.cache_path, key_to_filepath_converter=self.path_converter,
            key_to_file_node_converter=self.node_converter,
        )
        cache.initialize()
        cache.num_key_limit = 3
        cache.set_value(self.key2, self.value)
        self.assert_value_equal(cache.get_value(self.key1), self.value)
        self.assert_value_equal(cache.get_value(self.key2), self.value)

    def test_cleanup_by_creation_max1(self):
        self.cache.oldest_by = CREATED_INDEX_COL
        self.assert_key_in_cache(self.key1)
        self.cache.num_key_limit = 1
        self.assert_key_in_cache(self.key1)
        self.cache.set_value(self.key2, self.value)
        self.assert_key_in_cache(self.key2)
        self.assert_key_not_in_cache(self.key1)

    def test_cleanup_by_creation_max2(self):
        self.cache.num_key_limit = 2
        self.cache.oldest_by = CREATED_INDEX_COL
        self.assert_key_in_cache(self.key1)
        self.cache.set_value(self.key2, self.value)
        self.assert_key_in_cache(self.key2)
        self.cache.set_value(self.key3, self.value)
        self.assert_key_in_cache(self.key2)
        self.assert_key_in_cache(self.key3)
        self.assert_key_not_in_cache(self.key1)

    def test_cleanup_by_last_used(self):
        self.cache.num_key_limit = 2
        self.cache.oldest_by = LAST_USED_INDEX_COL
        self.assert_key_in_cache(self.key1)
        self.cache.set_value(self.key2, self.value)
        self.assert_key_in_cache(self.key2)
        self.cache.get_value(self.key1)
        self.cache.set_value(self.key3, self.value)
        self.assert_key_in_cache(self.key3)
        self.assert_key_in_cache(self.key1)
        self.assert_key_not_in_cache(self.key2)


def node_in_hdf5(filepath, node_path):
    """ Utility to test if a node is in an HDF5 file.
    """
    # Must be opened as "a" for compatibility with no index open file handle
    # functionality.
    with tb.open_file(filepath, "a") as h5file:
        return node_path in h5file
