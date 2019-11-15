""" Tests that serialization generate the expect data.
"""

from unittest import TestCase
import pandas as pd
import numpy as np
import datetime as dt
from six import PY3

from scimath.units.api import UnitArray, UnitScalar

from app_common.apptools.io.serialization_utils import \
    DEFAULT_ARR_HDF5_FILENAME, DEFAULT_PANDAS_HDF5_FILENAME
from app_common.apptools.io.serializer import serialize

if PY3:
    long = int


class TestSerializationBasicData(TestCase):

    def test_integers(self):
        obj = 1
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data'], obj)

        obj = long(12304987234230489237402983)
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data'], obj)

    def test_float(self):
        obj = 2.
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data'], obj)

    def test_float64(self):
        obj = np.float64(23.)
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data'], obj)

    def test_list(self):
        obj = [1, 2., "3"]
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data'], obj)

    def test_dict(self):
        obj = {1: "a", 2: "b", 3: "c"}
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data'], obj)

    def test_dict_with_lists(self):
        obj = {1: ["a", "b"], 2: [3, 4]}
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data'], obj)

    def test_dict_with_complex_obj(self):
        obj = {1: ("a", "b"), 2: (3, 4)}
        serial_data, array_collection = serialize(obj)
        self.assertIsInstance(serial_data['data'], dict)
        self.assertEqual(serial_data['data'].keys(), obj.keys())
        for val, source_val in zip(serial_data['data'].values(), obj.values()):
            self.assertEqual(val['class_metadata']["type"], "tuple")
            self.assertEqual(val['data'], list(source_val))

    def test_dict_with_complex_keys(self):
        obj = {("a", "b"): 1, (3, 4): 2}
        with self.assertRaises(NotImplementedError):
            serialize(obj)

    def test_tuple(self):
        """ Tuples serialize into a list"""
        obj = (1, 2., "3")
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data']['class_metadata']["type"],
                         "tuple")
        self.assertEqual(serial_data['data']['data'],
                         [1, 2., "3"])

    def test_set(self):
        obj = {"a", 1., 2, None}
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data']['class_metadata']["type"], "set")
        self.assertEqual(set(serial_data['data']['data']),
                         {'a', 1.0, 2, None})

    def test_datetime_date(self):
        obj = dt.date(2020, 1, 20)
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data']['class_metadata']["type"], "date")
        self.assertEqual(serial_data['data']['data'], [2020, 1, 20])

    def test_pandas_timestamp(self):
        # year, month, day, hour, minute, sec, microsec
        obj = pd.Timestamp(2020, 1, 20, 23, 59, 1, 10)
        serial_data, array_collection = serialize(obj)
        self.assertEqual(serial_data['data']['class_metadata']["type"],
                         "Timestamp")
        self.assertEqual(serial_data['data']['data'],
                         '2020-01-20 23:59:01.000010')

    def test_array(self):
        arr = np.array([1, 2, 3, 4.])
        serial_data, array_collection = serialize(arr)
        data = serial_data["data"]['class_metadata']
        self.assertEqual(data["filename"], DEFAULT_ARR_HDF5_FILENAME)
        self.assertEqual(data['type'], 'ndarray')
        assert_array_df_is_in_list(arr, array_collection)

    def test_unitarray(self):
        arr = np.array([1, 2, 3, 4])
        a = UnitArray(arr, units="m")

        serial_data, array_collection = serialize(a)
        metadata = serial_data["data"]['class_metadata']
        self.assertEqual(metadata["filename"], DEFAULT_ARR_HDF5_FILENAME)
        self.assertIn('id', metadata)
        self.assertIn('version', metadata)
        self.assertEqual(metadata['type'], 'UnitArray')
        # Only a copy of the array arr gets in the array collection
        # so we can only test for equality
        assert_array_df_copy_in_list(arr, array_collection.values())

        # Make sure the version bump was recorded in the object's metadata
        self.assertEqual(metadata["version"], 1)

    def test_smartunit(self):
        a = UnitScalar(1.0, units="m")
        unit = a.units
        serial_data, _ = serialize(unit)
        # metadata
        metadata = serial_data['data']['class_metadata']
        self.assertEqual(metadata['type'], 'SmartUnit')
        self.assertIn('id', metadata)
        self.assertIn('version', metadata)
        # data
        data = serial_data['data']['data']
        self.assertIsInstance(data, list)
        label, value, derivation, offset, valid = data
        self.assertEqual(label, 'm')
        self.assertEqual(value, 1.0)
        self.assertEqual(derivation['data'], [1, 0, 0, 0, 0, 0, 0])
        self.assertEqual(offset, 0.0)
        self.assertTrue(valid)

    def test_unitscalar(self):
        a = UnitScalar(1.0, units="m")
        serial_data, _ = serialize(a)
        data = serial_data['data']
        expected = ['data', 'units', 'class_metadata']
        self.assertEqual(set(data.keys()), set(expected))
        self.assertEqual(data['data'], 1.)
        self.assertEqual(data['units']["class_metadata"]['type'],
                         'SmartUnit')
        self.assertEqual(data['class_metadata']['type'], 'UnitScalar')

    def test_dataframe(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [1., 2., 3.]})
        serial_data, array_collection = serialize(df)
        data = serial_data["data"]['class_metadata']
        self.assertEqual(data["filename"], DEFAULT_PANDAS_HDF5_FILENAME)
        self.assertEqual(data['type'], 'DataFrame')
        assert_array_df_is_in_list(df, array_collection)


# Helper functions ------------------------------------------------------------

def assert_array_df_is_in_list(array, array_collection):
    """ Rewrite of the in operator because `in` seems to fail randomly with DF.

    FIXME: Re-evaluate with a newer pandas if this is still needed or if it can
    be replaced by assert df in array_collection.
    """
    equal = [array is elem for elem in array_collection.values()]
    assert any(equal)


def assert_array_df_copy_in_list(array, array_collection):
    array_type = type(array)
    array_shape = array.shape
    equals = []
    for elem in array_collection:
        if elem.shape == array_shape and isinstance(elem, array_type):
            equal = np.all(array == elem)
            equals.append(equal)
    assert any(equals)
