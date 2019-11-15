""" Test the storage and retrieval of various types of objects in a .chrom
project file.
"""

from unittest import TestCase
import os
import pandas as pd
import numpy as np
import datetime as dt

from scimath.units.api import UnitArray, UnitScalar

from app_common.apptools.io.assertion_utils import \
    assert_file_roundtrip_identical
from app_common.model_tools.data_element import DataElement

HERE = os.path.dirname(__file__)


class TestBasicDataFileStorage(TestCase):

    def test_int(self):
        obj = 2
        assert_file_roundtrip_identical(obj)

    def test_float(self):
        obj = 2.
        assert_file_roundtrip_identical(obj)

    def test_float64(self):
        obj = np.float64(23.)
        assert_file_roundtrip_identical(obj)

    def test_list(self):
        obj = ["1.", 2., 3]
        assert_file_roundtrip_identical(obj)

    def test_set(self):
        obj = {"1.", 2., 3}
        assert_file_roundtrip_identical(obj)

    def test_dict(self):
        obj = {"a": [1, 2, 3], "b": [1., 2., 3.]}
        assert_file_roundtrip_identical(obj)

    def test_datetime_date(self):
        obj = dt.date(2020, 1, 20)
        assert_file_roundtrip_identical(obj)

    def test_pandas_timestamp(self):
        # year, month, day, hour, minute, sec, microsec
        obj = pd.Timestamp(2020, 1, 20, 23, 59, 1, 10)
        assert_file_roundtrip_identical(obj)

    def test_array(self):
        obj = np.array([1, 2, 3, 4.])
        assert_file_roundtrip_identical(obj)

    def test_unitarray(self):
        arr = np.array([1, 2, 3, 4])
        obj = UnitArray(arr, units="m")
        assert_file_roundtrip_identical(obj)

    def test_smartunit(self):
        a = UnitScalar(1.0, units="m")
        unit = a.units
        assert_file_roundtrip_identical(unit)

    def test_unitscalar(self):
        a = UnitScalar(1.0, units="m")
        assert_file_roundtrip_identical(a)

    def test_series(self):
        s = pd.Series({"a": 1, "b": 2.})
        assert_file_roundtrip_identical(s)

    def test_dataframe(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [1., 2., 3.]})
        assert_file_roundtrip_identical(df)


class TestHighLevelFileStorage(TestCase):
    """ Test of high level functions save_object and load_object.
    """
    def test_write_read_raw_data_element(self):
        data = DataElement(name="blah")
        assert_file_roundtrip_identical(data)
