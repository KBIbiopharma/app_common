from os.path import dirname
from unittest import TestCase
import numpy as np
from numpy.testing import assert_array_equal

from app_common.apptools.cache.single_array_hdf_cache import \
    HDF5SingleArrayCache, HDF5SingleArrayNoIndexCache
from app_common.apptools.cache.base_hdf_cache import KeyFormatError
from app_common.apptools.cache.base_test_classes import BaseHDF5Cache, \
    BaseHDF5CacheFromScratch, DEFAULT_VALUE_GROUP, \
    BaseHDF5CacheFromScratchNoIndex, BaseHDF5CacheNoIndex

HERE = dirname(__file__)

SAMPLE_ARRAY = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])


class TestHDF5SingleArrayCacheFromScratch(BaseHDF5CacheFromScratch, TestCase):
    def setUp(self):
        super(TestHDF5SingleArrayCacheFromScratch, self).setUp()
        self.cache_klass = HDF5SingleArrayCache
        self.value = SAMPLE_ARRAY

    def assert_value_equal(self, val1, val2):
        assert_array_equal(val1, val2)


class TestHDF5SingleArrayCache(BaseHDF5Cache, TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestHDF5SingleArrayCache, cls).setUpClass()
        cls.cache_klass = HDF5SingleArrayCache
        cls.value = SAMPLE_ARRAY
        cls.value2 = cls.value + 1
        cls.key1 = "/abc/def"
        cls.key2 = "/blah/foo"
        cls.node_leaf_name = "def"

    def setUp(self):
        # Keys are of the the form /FILENAME/NODE_NAME:
        self.path_converter = lambda x: x.split("/")[1] + ".h5"
        self.node_converter = \
            lambda x: "/" + DEFAULT_VALUE_GROUP + "/" + x.split("/")[-1]

        super(TestHDF5SingleArrayCache, self).setUp()

    # Implementation specific tests -------------------------------------------

    def test_df_hdf_cache_set_bad_key(self):
        # Bad formatting of the key w.r.t. node_converter:
        with self.assertRaises(KeyFormatError):
            self.cache.set_value("blah", self.value)


class TestHDF5SingleArrayNoIndexCacheFromScratch(
        BaseHDF5CacheFromScratchNoIndex, TestCase):

    def setUp(self):
        super(TestHDF5SingleArrayNoIndexCacheFromScratch, self).setUp()
        self.cache_klass = HDF5SingleArrayNoIndexCache
        self.value = SAMPLE_ARRAY

    def assert_value_equal(self, val1, val2):
        assert_array_equal(val1, val2)


class TestHDF5SingleArrayNoIndexCache(BaseHDF5CacheNoIndex, TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestHDF5SingleArrayNoIndexCache, cls).setUpClass()
        cls.cache_klass = HDF5SingleArrayNoIndexCache
        cls.value = SAMPLE_ARRAY
        cls.value2 = cls.value + 1
        cls.key1 = "/abc/def"
        cls.key2 = "/blah/foo"
        cls.node_leaf_name = "def"

    def setUp(self):
        # Keys are of the the form /FILENAME/NODE_NAME:
        self.path_converter = lambda x: x.split("/")[1] + ".h5"
        self.node_converter = \
            lambda x: "/" + DEFAULT_VALUE_GROUP + "/" + x.split("/")[-1]

        super(TestHDF5SingleArrayNoIndexCache, self).setUp()

    # Implementation specific tests -------------------------------------------

    def test_df_hdf_cache_set_bad_key(self):
        # Bad formatting of the key w.r.t. node_converter:
        with self.assertRaises(KeyFormatError):
            self.cache.set_value("blah", self.value)
