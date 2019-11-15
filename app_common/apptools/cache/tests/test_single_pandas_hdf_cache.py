from os.path import dirname, isfile, join
from unittest import TestCase
import pandas as pd
from pandas.util.testing import assert_frame_equal

from app_common.apptools.cache.single_pandas_hdf_cache import \
    DEFAULT_HDF_DATA_KEY, HDF5SinglePandasCache
from app_common.apptools.cache.base_test_classes import BaseHDF5Cache, \
    BaseHDF5CacheFromScratch

HERE = dirname(__file__)


class TestHDF5SinglePandasCacheFromScratch(BaseHDF5CacheFromScratch, TestCase):
    def setUp(self):
        super(TestHDF5SinglePandasCacheFromScratch, self).setUp()
        self.cache_klass = HDF5SinglePandasCache
        self.value = pd.DataFrame({"a": range(5), "b": list("abcde")})

    def assert_value_equal(self, val1, val2):
        assert_frame_equal(val1, val2)


class TestHDF5SinglePandasCache(BaseHDF5Cache, TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestHDF5SinglePandasCache, cls).setUpClass()
        cls.cache_klass = HDF5SinglePandasCache
        cls.value = pd.DataFrame({"a": range(5), "b": list("abcde")})
        cls.value2 = pd.DataFrame({"a": range(5), "b": list("xyzab")})
        cls.key1 = "abc"
        cls.key2 = "blah"

    def setUp(self):
        # These callables can't be added as class methods:
        self.path_converter = lambda x: x + ".h5"
        self.node_converter = lambda x: "/" + DEFAULT_HDF_DATA_KEY

        super(TestHDF5SinglePandasCache, self).setUp()

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
