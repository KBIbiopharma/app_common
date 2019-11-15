""" Tests for the utility functions in param_trait_search module.
"""

from unittest import skipUnless, TestCase
import numpy as np
import pandas as pd

try:
    from scimath.units.api import UnitArray, UnitScalar
    SCIMATH_AVAILABLE = True
except ImportError:
    SCIMATH_AVAILABLE = False

from traits.api import Any, Float, HasTraits, List, Str

if SCIMATH_AVAILABLE:
    from app_common.traits.param_trait_search import \
        search_parameters_in_data, search_parameters_in_dict, \
        search_parameters_in_sequence
    from app_common.traits.custom_trait_factories import Parameter, \
        ParameterArray, ParameterFloat, ParameterInt, ParameterUnitArray
    from app_common.model_tools.data_element import DataElement


EQUAL = (True, "")


class B_HT(HasTraits):
    """ Testing subclass, inherit from HasTraits.
    """
    b_int = ParameterInt()
    name = Str("new B")
    type_id = Str("B")


class B_DE(DataElement):
    """ Testing subclass, inherit from DataElement, so searchable.
    """
    b_int = ParameterInt()
    name = Str("new B")
    type_id = Str("B")


if SCIMATH_AVAILABLE:
    class A(DataElement):
        """ Testing class"""
        name = Str("new A")
        type_id = Str("A")
        a_int = ParameterInt
        a_float = ParameterFloat
        a_list = List()
        a_array = ParameterArray
        a_uarray = ParameterUnitArray
        a_uscalar = Parameter
        a_obj = Any
        a_noparam = Float


@skipUnless(SCIMATH_AVAILABLE, "scimath not available")
class TestSearchParameters(TestCase):
    def setUp(self):
        uscal = UnitScalar(1, units="cm")
        uarr = UnitArray([1, 2, 3], units="cm")
        b = B_HT(b_int=3)
        self.data = {"a_int": 1, "a_float": 1., "a_list": list(range(5)),
                     "a_array": np.arange(4), "a_uarray": uarr,
                     "a_uscalar": uscal, "a_obj": b, "a_noparam": 2.}
        self.a_obj = A(**self.data)
        self.expected = {'a_array[0]', 'a_array[1]', 'a_array[2]',
                         'a_array[3]', 'a_uarray[0]', 'a_uarray[1]',
                         'a_uarray[2]', 'a_float', 'a_int', 'a_uscalar',
                         'a_obj.b_int'}

        b2 = B_DE(b_int=3)
        self.data = {"a_int": 1, "a_float": 1., "a_list": list(range(5)),
                     "a_array": np.arange(4), "a_uarray": uarr,
                     "a_uscalar": uscal, "a_obj": b2, "a_noparam": 2.}
        self.a2_obj = A(**self.data)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_search_parameters_in_data(self):
        params = search_parameters_in_data(self.a_obj)
        # a_obj attribute is a straight HT instance, not DataElement:
        expected = self.expected - {'a_obj.b_int'}
        self.assertEqual(set(params), set(expected))

    def test_search_parameters_in_data_with_data_subclass(self):
        """ Same as above, but B attribute derives from DataElement so is
        parsed.
        """
        params = search_parameters_in_data(self.a2_obj)
        self.assertEqual(set(params), set(self.expected))

    def test_search_parameters_in_list(self):
        params = search_parameters_in_sequence([])
        self.assertEqual(params, [])

        params = search_parameters_in_sequence([self.a2_obj])
        expected = ["[0]." + elem for elem in self.expected]
        self.assertEqual(set(params), set(expected))

    def test_search_parameters_in_tuple(self):
        params = search_parameters_in_sequence(tuple())
        self.assertEqual(params, [])

        params = search_parameters_in_sequence((self.a2_obj,))
        expected = ["[0]." + elem for elem in self.expected]
        self.assertEqual(set(params), set(expected))

    def test_search_parameters_in_set(self):
        with self.assertRaises(ValueError):
            search_parameters_in_sequence(set())

    def test_search_parameters_in_dict(self):
        params = search_parameters_in_dict({})
        self.assertEqual(params, [])

        params = search_parameters_in_dict({'a': self.a2_obj})
        expected = ["['a']." + elem for elem in self.expected]
        self.assertEqual(set(params), set(expected))

    def test_search_parameters_in_series(self):
        params = search_parameters_in_sequence(pd.Series())
        self.assertEqual(params, [])

        s = pd.Series([self.a2_obj], index=['a'])
        params = search_parameters_in_sequence(s)
        expected = ["[0]." + elem for elem in self.expected]
        self.assertEqual(set(params), set(expected))
