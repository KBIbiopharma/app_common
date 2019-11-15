
from os.path import dirname, isfile, join
from unittest import TestCase
import pandas as pd
import numpy as np
from pandas.util.testing import assert_frame_equal
from numpy.testing import assert_array_equal
import tables as tb

from app_common.apptools.cache.base_hdf_cache import DEFAULT_HDF_DATA_KEY, \
    KeyFormatError
from app_common.apptools.cache.timestamped_hdf_caches import \
    TimestampedSingleArrayCache, TimestampedSinglePandasCache
from app_common.apptools.cache.base_test_classes import \
    BaseHDF5CacheFromScratch, BaseTimestampedCacheMetadataTests, \
    DEFAULT_VALUE_GROUP, node_in_hdf5

HERE = dirname(__file__)

DEFAULT_DF = pd.DataFrame({"a": range(5), "b": list("abcde")})

DEFAULT_ARRAY = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])


class TestHDFTSPandasCacheFromScratch(BaseHDF5CacheFromScratch, TestCase):
    def setUp(self):
        super(TestHDFTSPandasCacheFromScratch, self).setUp()
        self.cache_klass = TimestampedSinglePandasCache
        self.value = DEFAULT_DF

    def assert_value_equal(self, val1, val2):
        assert_frame_equal(val1, val2)


class TestHDFTSArrayCacheFromScratch(BaseHDF5CacheFromScratch, TestCase):
    def setUp(self):
        super(TestHDFTSArrayCacheFromScratch, self).setUp()
        self.cache_klass = TimestampedSingleArrayCache
        self.value = DEFAULT_ARRAY

    def assert_value_equal(self, val1, val2):
        assert_array_equal(val1, val2)


class TestHDFTSPandasCache(BaseTimestampedCacheMetadataTests, TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestHDFTSPandasCache, cls).setUpClass()
        cls.cache_klass = TimestampedSinglePandasCache
        cls.value = DEFAULT_DF
        cls.value2 = pd.DataFrame({"a": range(5), "b": list("xyzab")})
        cls.key1 = "abc"
        cls.key2 = "blah"

    def setUp(self):
        # These callables can't be added as class methods:
        self.path_converter = lambda x: join(self.cache_path, x + ".h5")
        self.node_converter = lambda x: DEFAULT_HDF_DATA_KEY

        super(TestHDFTSPandasCache, self).setUp()

    # Implementation specific tests -------------------------------------------

    # Helper methods ----------------------------------------------------------

    def assert_key_in_cache(self, key):
        self.assertIn(key, self.cache)
        expected_filename = self.path_converter(key)
        expected_filepath = join(self.cache_path, expected_filename)
        self.assertTrue(isfile(expected_filepath))

    def assert_key_not_in_cache(self, key):
        self.assertNotIn(key, self.cache)
        expected_filename = self.path_converter(key)
        expected_filepath = join(self.cache_path, expected_filename)
        self.assertFalse(isfile(expected_filepath))

    def assert_value_equal(self, val1, val2):
        assert_frame_equal(val1, val2)

    def create_cache_content(self):
        with pd.HDFStore(self.hdf_fpath, "w") as store:
            self.value.to_hdf(store, DEFAULT_HDF_DATA_KEY)


class TestHDFTSArrayCache(BaseTimestampedCacheMetadataTests, TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestHDFTSArrayCache, cls).setUpClass()
        cls.cache_klass = TimestampedSingleArrayCache
        cls.value = DEFAULT_ARRAY
        cls.value2 = cls.value + 1
        cls.key1 = "/abc/def"
        cls.key2 = "/blah/foo"
        cls.node_leaf_name = "def"

    def setUp(self):
        # Keys are of the the form /FILENAME/NODE_NAME:
        self.path_converter = lambda x: x.split("/")[1] + ".h5"
        self.node_converter = \
            lambda x: "/" + DEFAULT_VALUE_GROUP + "/" + x.split("/")[2]

        super(TestHDFTSArrayCache, self).setUp()

    # Implementation specific tests -------------------------------------------

    def test_df_hdf_cache_set_bad_key(self):
        # Bad formatting of the key w.r.t. node_converter:
        with self.assertRaises(KeyFormatError):
            self.cache.set_value("blah", self.value)

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
        with tb.open_file(self.hdf_fpath, "w") as h5file:
            h5file.create_group("/", DEFAULT_VALUE_GROUP)
            h5_filter = tb.Filters(complib="blosc", complevel=9)
            h5file.create_carray("/"+DEFAULT_VALUE_GROUP, self.node_leaf_name,
                                 obj=self.value, filters=h5_filter)
