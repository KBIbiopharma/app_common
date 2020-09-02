""" Tests for the utility functions in has_traits_utils module. """

from unittest import skipUnless, TestCase
import numpy as np
from uuid import UUID

try:
    from scimath.units.api import UnitArray, UnitScalar
    SCIMATH_AVAILABLE = True
except ImportError:
    SCIMATH_AVAILABLE = False

from traits.api import Array, Bool, cached_property, Dict, Float, HasTraits, \
    Instance, Int, List, Property, Str

if SCIMATH_AVAILABLE:
    from app_common.traits.has_traits_utils import is_has_traits_almost_equal,\
        is_val_almost_equal, trait_dict

EQUAL = (True, "")

if SCIMATH_AVAILABLE:
    class A(HasTraits):
        """ Testing class
        """
        a_list = List([1, 2, 3])
        a_array = Array(value=np.arange(10))
        name = Str("sdfsjhd")
        editable = Bool
        a_uarray = Instance(UnitArray)
        _unique_keys = Dict()
        a_int = Int(6)
        a_uscalar = Instance(UnitScalar)
        a_float = Float(1.2)
        uuid = Instance(UUID)


class B(HasTraits):
    """ Testing class
    """
    b_int = Int
    y = Float(4)
    z = Str("sdfgkjshd")


class C(HasTraits):
    """ Testing class which contains another locally defined one.
    """
    x = Int
    sub_attr = Instance(B, ())
    y = Property(Int, depends_on="sub_attr")

    @cached_property
    def _get_y(self):
        return self.sub_attr.b_int


class D(HasTraits):
    x = Float


class E(HasTraits):
    a = Array


@skipUnless(SCIMATH_AVAILABLE, "scimath not available")
class TestTraitDict(TestCase):

    def test_simplest_class(self):
        self.assertEqual(trait_dict(D()), {"x": 0})

    def test_simple_class_with_property(self):
        c_content = trait_dict(C(x=2))
        expected_keys = {"x", "sub_attr"}
        self.assertEqual(set(c_content.keys()), expected_keys)
        self.assertEqual(c_content["x"], 2)

    def test_large_class(self):
        a_content = trait_dict(A(a_int=2))
        expected_keys = {'a_list', 'a_array', 'name', 'editable', 'a_uarray',
                         '_unique_keys', 'a_int', 'a_uscalar', 'a_float',
                         'uuid'}
        self.assertEqual(set(a_content.keys()), expected_keys)
        self.assertEqual(a_content["a_int"], 2)


@skipUnless(SCIMATH_AVAILABLE, "scimath not available")
class TestIsHasTraitsAlmostEqual(TestCase):
    def test_identical_objects(self):
        # Simplest HT class
        b = B()
        self.assertEqual(is_has_traits_almost_equal(b, b), EQUAL)

        # HT class with Parameters
        a = A()
        self.assertEqual(is_has_traits_almost_equal(a, a), EQUAL)

        # With nested objects
        a = A(a_chrom_obj=b)
        self.assertEqual(is_has_traits_almost_equal(a, a), EQUAL)

    def test_fail_from_type(self):
        b = B()
        a = A()
        self.assertEqual(is_has_traits_almost_equal(a, b),
                         (False, 'Different types (A vs B)'))

    def test_fail_from_none(self):
        # a's a_chrom_obj is None since not initialized
        a1 = A()
        a2 = A(a_chrom_obj=B())
        self.assertFalse(is_has_traits_almost_equal(a1, a2)[0])
        # This will trigger a comparison of a.a_chrom_obj and b.a_chrom_obj
        self.assertFalse(is_has_traits_almost_equal(a2, a1)[0])

    def test_fail_from_extra_attrs(self):
        c1 = C()
        c2 = C()
        c2.foo = 2
        self.assertEqual(is_has_traits_almost_equal(c1, c2),
                         (False, "Different trait content: foo"))

    def test_cloned_objects(self):
        a = A()
        a_clone = a.clone_traits()
        self.assertEqual(is_has_traits_almost_equal(a, a_clone), EQUAL)

    def test_list_in_objects(self):
        a = A(a_list=[1, 4.])
        # Same list but int instead of float
        a2 = A(a_list=[1, 4])
        self.assertEqual(is_has_traits_almost_equal(a, a2), EQUAL)
        a3 = A(a_list=[1, 1])
        equal, msg = is_has_traits_almost_equal(a, a3)
        self.assertFalse(equal)
        self.assertTrue(msg.startswith('Different a_list[1]'))

    def test_list_of_objects_in_objects(self):
        a = A(a_list=[A(a_list=[1, 4.])])
        # Same list but int instead of float
        a2 = A(a_list=[A(a_list=[1, 4])])
        self.assertEqual(is_has_traits_almost_equal(a, a2), EQUAL)
        a3 = A(a_list=[A(a_list=[1, 1])])
        equal, msg = is_has_traits_almost_equal(a, a3)
        self.assertFalse(equal)
        self.assertTrue(msg.startswith('Different a_list[0].a_list[1]'))

    def test_differ_by_property_cache(self):
        c1 = C(x=1, sub_attr=B())
        # Trigger creation of cache attribute
        _ = c1.y

        # Copy the 2 objects manually: the cache attribute will become part of
        # the trait_names
        c2 = C()
        for attr, val in c1.__dict__.items():
            if not attr.startswith("__traits"):
                setattr(c2, attr, val)

        # Remove the cache attribute from c1 only and make sure the 2 objects
        # are still considered "almost" equal.
        delattr(c1, "_traits_cache_y")
        self.assertNotIn("_traits_cache_y", c1.trait_names())
        self.assertIn("_traits_cache_y", c2.trait_names())
        self.assertEqual(is_has_traits_almost_equal(c1, c2), EQUAL)

    def test_differ_but_ignore(self):
        c1 = C(x=1)
        c2 = C(x=2)
        self.assertNotEqual(is_has_traits_almost_equal(c1, c2), EQUAL)
        self.assertEqual(is_has_traits_almost_equal(c1, c2, ignore=['x']),
                         EQUAL)

        # Test ignoring nested attributes
        c1 = C(x=1, sub_attr=B(b_int=1))
        c2 = C(x=1, sub_attr=B(b_int=2))
        self.assertNotEqual(is_has_traits_almost_equal(c1, c2), EQUAL)
        self.assertEqual(is_has_traits_almost_equal(c1, c2, ignore=['b_int']),
                         EQUAL)

    def test_array_dtype(self):
        e1 = E(a=np.array([1, 2], dtype=int))
        e2 = E(a=np.array([1., 2.], dtype=float))
        self.assertEqual(is_has_traits_almost_equal(e1, e2), EQUAL)
        is_equal = is_has_traits_almost_equal(e1, e2, check_dtype=True)
        self.assertNotEqual(is_equal, EQUAL)


@skipUnless(SCIMATH_AVAILABLE, "scimath not available")
class TestIsValAlmostEqual(TestCase):
    def test_list(self):
        l1 = [D(x=2.0), D(x=1.0)]
        l2 = [D(x=1+1), D(x=1.0)]
        self.assertEqual(is_val_almost_equal(l1, l2), EQUAL)

        l3 = [D(x=2.0 + 1.e-10), D(x=1.0)]
        # By default differences that are smaller than 1e-9 are ignored
        self.assertEqual(is_val_almost_equal(l1, l3), EQUAL)
        # with higher precision, it should fail:
        equal, msg = is_val_almost_equal(l1, l3, eps=1e-11)
        self.assertFalse(equal)
        self.assertTrue(msg.startswith('Different [0].x'))

    def test_array(self):
        a1 = np.array([1, 2, 3, 4])
        a2 = np.array([1., 2., 3., 4.])
        self.assertEqual(is_val_almost_equal(a1, a2), EQUAL)

        a1 = np.array(list("abcde"))
        a2 = np.array(list("abcde"))
        self.assertEqual(is_val_almost_equal(a1, a2), EQUAL)

    def test_array_different_int_dtype(self):
        a1 = np.array([1, 2, 3, 4], dtype="int32")
        a2 = np.array([1, 2, 3, 4], dtype="int64")
        self.assertEqual(is_val_almost_equal(a1, a2), EQUAL)
        self.assertFalse(is_val_almost_equal(a1, a2, check_dtype=True)[0])

    def test_array_different_str_dtype(self):
        a1 = np.array(list("abcde"), dtype='|S1')
        a2 = np.array(list("abcde"), dtype='|S2')
        self.assertEqual(is_val_almost_equal(a1, a2), EQUAL)
        self.assertFalse(is_val_almost_equal(a1, a2, check_dtype=True)[0])
