""" Tests that serialization generate the expect data.
"""

from unittest import TestCase
import pandas as pd
import numpy as np
import datetime as dt
from six import PY3

from scimath.units.api import UnitArray, UnitScalar

from app_common.apptools.io.assertion_utils import assert_roundtrip_identical

if PY3:
    long = int


class TestSerializationBasicData(TestCase):

    def test_integers(self):
        obj = 2
        assert_roundtrip_identical(obj)

        obj = long(12304987234230489237402983)
        assert_roundtrip_identical(obj)

    def test_float(self):
        obj = 2.
        assert_roundtrip_identical(obj)

        obj = np.float64(23.)
        assert_roundtrip_identical(obj)

    def test_list(self):
        obj = ["1.", 2., 3]
        assert_roundtrip_identical(obj)

    def test_set(self):
        obj = {"1.", 2., 3, None}
        assert_roundtrip_identical(obj)

    def test_dict(self):
        obj = {"a": [1, 2, 3], "b": [1., 2., 3.]}
        assert_roundtrip_identical(obj)

    def test_dict_with_complex_obj(self):
        obj = {1: ("a", "b"), 2: (3, 4)}
        assert_roundtrip_identical(obj)

    def test_dict_with_complex_keys(self):
        obj = {("a", "b"): 1, (3, 4): 2}
        with self.assertRaises(NotImplementedError):
            assert_roundtrip_identical(obj)

    def test_datetime_date(self):
        obj = dt.date(2020, 1, 20)
        assert_roundtrip_identical(obj)

    def test_pandas_timestamp(self):
        # year, month, day, hour, minute, sec, microsec
        obj = pd.Timestamp(2020, 1, 20, 23, 59, 1, 10)
        assert_roundtrip_identical(obj)

    def test_array(self):
        obj = np.array([1, 2, 3, 4.])
        assert_roundtrip_identical(obj)

    def test_unitarray(self):
        arr = np.array([1, 2, 3, 4])
        obj = UnitArray(arr, units="m")
        assert_roundtrip_identical(obj)

    def test_smartunit(self):
        a = UnitScalar(1.0, units="m")
        unit = a.units
        assert_roundtrip_identical(unit)

    def test_unitscalar(self):
        a = UnitScalar(1.0, units="m")
        assert_roundtrip_identical(a)

    def test_series(self):
        s = pd.Series({"a": 1, "b": 2.})
        assert_roundtrip_identical(s)

    def test_dataframe(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [1., 2., 3.]})
        assert_roundtrip_identical(df)
