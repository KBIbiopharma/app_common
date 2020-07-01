from unittest import TestCase
from numpy.testing import assert_allclose

from scimath.units.api import UnitArray, UnitScalar
from scimath.units.length import meter
from scimath.units.unit import InvalidConversion

from app_common.scimath.units_utils import convert_units, \
    unit_scalars_almost_equal, units_almost_equal, unitarray_to_unitted_list, \
    unitted_list_to_array, has_mass_units, has_volume_units, \
    has_same_unit_type_as
from app_common.scimath.assertion_utils import assert_unit_array_almost_equal,\
    assert_unit_scalar_almost_equal
from app_common.scimath import more_units


class TestConvertUnits(TestCase):

    # Tests -------------------------------------------------------------------

    def test_scalar_convert_units(self):
        scalar_data = UnitScalar(1, units=more_units.length.m)
        conv_data = convert_units(scalar_data, more_units.length.cm)
        self.assertEqual(conv_data,
                         UnitScalar(100, units=more_units.length.cm))

        # convert back to original units and check
        conv_data_2 = convert_units(conv_data, scalar_data.units)
        self.assertEqual(conv_data_2, scalar_data)

    def test_array_convert_units(self):
        array_data = UnitArray([1, 2, 3], units=more_units.length.m)
        conv_data = convert_units(array_data, more_units.length.cm)
        assert_allclose(conv_data.tolist(), (100 * array_data).tolist())
        self.assertEqual(conv_data.units, more_units.length.cm)

        # convert back to original units and check
        conv_data_2 = convert_units(conv_data, array_data.units)
        assert_allclose(conv_data_2.tolist(), array_data.tolist())
        self.assertEqual(conv_data_2.units, array_data.units)

    def test_invalid_arguments(self):
        scalar_data = UnitScalar(1, units=more_units.length.m)

        # raise error if the units are not consistent
        with self.assertRaises(InvalidConversion):
            convert_units(scalar_data, more_units.volume.liter)

        # raise error if the data does not have units
        with self.assertRaises(ValueError):
            convert_units(1, more_units.volume.liter)


class TestAssertUnitScalarEqual(TestCase):
    def test_same_unit_scalar(self):
        assert_unit_scalar_almost_equal(UnitScalar(1, units="s"),
                                        UnitScalar(1, units="s"))

    def test_equivalent_unit_scalar(self):
        assert_unit_scalar_almost_equal(UnitScalar(1, units="m"),
                                        UnitScalar(100, units="cm"))


class TestAssertUnitArrayEqual(TestCase):
    def test_same_unit_array(self):
        assert_unit_array_almost_equal(UnitArray([1, 2], units="s"),
                                       UnitArray([1, 2], units="s"))

    def test_equivalent_unit_array(self):
        assert_unit_array_almost_equal(UnitArray([1, 2], units="m"),
                                       UnitArray([100, 200], units="cm"))


class TestUnittedListToArray(TestCase):

    def test_homogeneous_list(self):
        input_list = [UnitScalar(1, units="m"), UnitScalar(2, units="m")]
        arr = unitted_list_to_array(input_list)
        assert_unit_array_almost_equal(arr, UnitArray([1, 2], units="m"))

    def test_list_mixed_unit_spelling(self):
        input_list = [UnitScalar(1, units="m"), UnitScalar(2, units=meter)]
        arr = unitted_list_to_array(input_list)
        assert_unit_array_almost_equal(arr, UnitArray([1, 2], units="m"))

    def test_list_mixed_unit(self):
        input_list = [UnitScalar(1., units="m"), UnitScalar(200., units="cm")]
        arr = unitted_list_to_array(input_list)
        assert_unit_array_almost_equal(arr, UnitArray([1., 2.], units="m"))

    def test_list_mixed_unit_request_unit(self):
        input_list = [UnitScalar(1., units="m"), UnitScalar(200., units="cm")]
        arr = unitted_list_to_array(input_list, target_unit="mm")
        assert_unit_array_almost_equal(arr, UnitArray([1000., 2000.],
                                                      units="mm"))

    def test_inhomogeneous__incompatible_list(self):
        input_list = [UnitScalar(1, units="m"), UnitScalar(2, units="liter")]
        with self.assertRaises(ValueError):
            unitted_list_to_array(input_list)


class TestUnitarrayToUnittedList(TestCase):

    def test_conversion(self):
        input_list = UnitArray([1, 2], units="m")
        list_data = unitarray_to_unitted_list(input_list)
        self.assertEqual(list_data,
                         [UnitScalar(1, units="m"), UnitScalar(2, units="m")])


class TestUnitScalarAlmostEqual(TestCase):
    def test_values_identical(self):
        val1 = UnitScalar(1., units="m")
        self.assertTrue(unit_scalars_almost_equal(val1, val1))

    def test_values_identical_in_diff_units(self):
        val1 = UnitScalar(1., units="m")
        val2 = UnitScalar(100., units="cm")
        self.assertTrue(unit_scalars_almost_equal(val1, val2))

    def test_values_close_enough(self):
        val1 = UnitScalar(1., units="m")
        val2 = val1 + UnitScalar(1.e-5, units="m")
        self.assertFalse(unit_scalars_almost_equal(val1, val2))
        self.assertTrue(unit_scalars_almost_equal(val1, val2, eps=1e-4))


class TestUnitHasMassUnits(TestCase):
    def test_straight_mass(self):
        val1 = UnitScalar(1., units="g")
        self.assertTrue(has_mass_units(val1.units))

        val1 = UnitScalar(1., units="kg")
        self.assertTrue(has_mass_units(val1.units))

    def test_not_mass(self):
        val1 = UnitScalar(1., units="meter")
        self.assertFalse(has_mass_units(val1.units))

        val1 = UnitScalar(1., units=meter)
        self.assertFalse(has_mass_units(val1.units))

    def test_mass_equivalent(self):
        val1 = UnitScalar(1., units="g/liter")
        val2 = UnitScalar(1., units="m**3")
        product = val1 * val2
        self.assertTrue(has_mass_units(product.units))


class TestUnitHasVolumeUnits(TestCase):
    def test_straight_volume(self):
        val1 = UnitScalar(1., units="liter")
        self.assertTrue(has_volume_units(val1.units))

        val1 = UnitScalar(1., units="m**3")
        self.assertTrue(has_volume_units(val1.units))

    def test_not_volume(self):
        val1 = UnitScalar(1., units="meter")
        self.assertFalse(has_volume_units(val1.units))

        val1 = UnitScalar(1., units=meter)
        self.assertFalse(has_volume_units(val1.units))

    def test_vol_equivalent(self):
        val1 = UnitScalar(1., units="cm")
        val2 = UnitScalar(1., units="m**2")
        product = val1 * val2
        self.assertTrue(has_volume_units(product.units))


class TestUnitsAlmostEqual(TestCase):
    def test_almost_equal_same_unitscalar(self):
        val1 = UnitScalar(1., units="cm")
        self.assertTrue(units_almost_equal(val1, val1))

    def test_almost_equal_same_unit(self):
        val1 = UnitScalar(1., units="cm")
        self.assertTrue(units_almost_equal(val1.units, val1.units))

    def test_not_almost_equal_different_value(self):
        val1 = UnitScalar(1., units=meter)
        val2 = UnitScalar(100., units="cm")

        # Values are equal, but units are not:
        self.assertFalse(units_almost_equal(val1, val2))

    def test_almost_equal_different_value(self):
        val1 = UnitScalar(1., units="g/liter")
        val2 = UnitScalar(1., units="kg/m**3")

        # Values are equal, but units are not:
        self.assertTrue(units_almost_equal(val1, val2))

    def test_almost_equal_dimensionless_vals(self):
        # Make dimensionless quantities:
        val1 = UnitScalar(1., units="BLAH")

        # Values are equal, but units are not:
        self.assertTrue(units_almost_equal(val1.units, val1.units))

    def test_almost_equal_dimensionless_vals_check_label(self):
        # Make dimensionless quantities:
        val1 = UnitScalar(1., units="BLAH")
        val2 = UnitScalar(1., units="FOO")

        # Values are equal, but units are not:
        self.assertFalse(units_almost_equal(val1.units, val2.units))


class TestUnitsSameType(TestCase):
    def test_same_type_same_unitscalar(self):
        val1 = UnitScalar(1., units="cm")
        self.assertTrue(has_same_unit_type_as(val1, val1))

    def test_same_type_same_unit(self):
        val1 = UnitScalar(1., units="cm")
        self.assertTrue(has_same_unit_type_as(val1.units, val1.units))

    def test_same_type_units(self):
        val1 = UnitScalar(1., units=meter)
        val2 = UnitScalar(1., units="cm")

        # Values are equal, but units are not:
        self.assertTrue(has_same_unit_type_as(val1.units, val2.units))

    def test_same_type_str(self):
        val1 = UnitScalar(1., units=meter)

        # Values are equal, but units are not:
        self.assertTrue(has_same_unit_type_as(val1.units, "cm"))

        val1 = UnitScalar(1., units="s")

        # Values are equal, but units are not:
        self.assertTrue(has_same_unit_type_as(val1.units, "minute"))

    def test_same_type_unit_scalar(self):
        val1 = UnitScalar(1., units=meter)
        val2 = UnitScalar(1., units="cm")

        # Values are equal, but units are not:
        self.assertTrue(has_same_unit_type_as(val1, val2))

    def test_same_type_different_value(self):
        val1 = UnitScalar(1., units=meter)
        val2 = UnitScalar(100., units="cm")

        # Values are equal, but units are not:
        self.assertTrue(has_same_unit_type_as(val1, val2))

    def test_same_type_composite_unit(self):
        val1 = UnitScalar(1., units="g/liter")
        val2 = UnitScalar(1., units="kg/m**3")

        # Values are equal, but units are not:
        self.assertTrue(has_same_unit_type_as(val1.units, val2.units))

    def test_same_type_composite_unit_str(self):
        val1 = UnitScalar(1., units="g/liter")

        # Values are equal, but units are not:
        self.assertTrue(has_same_unit_type_as(val1.units, "kg/m**3"))

    def test_same_type_composite_unit_unit_scalar(self):
        val1 = UnitScalar(1., units="g/liter")
        val2 = UnitScalar(1., units="kg/m**3")

        # Values are equal, but units are not:
        self.assertTrue(has_same_unit_type_as(val1, val2))

    def test_not_same_type(self):
        val1 = UnitScalar(1., units=meter)
        val2 = UnitScalar(1., units="g")

        # Values are equal, but units are not:
        self.assertFalse(has_same_unit_type_as(val1.units, val2.units))

        val1 = UnitScalar(1., units="s")
        val2 = UnitScalar(1., units="kg")

        # Values are equal, but units are not:
        self.assertFalse(has_same_unit_type_as(val1.units, val2.units))

    def test_not_same_type_str(self):
        val1 = UnitScalar(1., units=meter)

        # Values are equal, but units are not:
        self.assertFalse(has_same_unit_type_as(val1.units, "g"))

        val1 = UnitScalar(1., units="s")

        # Values are equal, but units are not:
        self.assertFalse(has_same_unit_type_as(val1.units, "kg"))

    def test_not_same_type_unit_scalar(self):
        val1 = UnitScalar(1., units=meter)
        val2 = UnitScalar(1., units="g")

        # Values are equal, but units are not:
        self.assertFalse(has_same_unit_type_as(val1, val2))

        val1 = UnitScalar(1., units="s")
        val2 = UnitScalar(1., units="kg")

        # Values are equal, but units are not:
        self.assertFalse(has_same_unit_type_as(val1, val2))

    def test_not_same_type_unit_arrays(self):
        val1 = UnitArray([1.], units=meter)
        val2 = UnitArray([1.], units="g")

        # Values are equal, but units are not:
        self.assertFalse(has_same_unit_type_as(val1, val2))

        val1 = UnitArray([1.], units="s")
        val2 = UnitArray([1.], units="kg")

        # Values are equal, but units are not:
        self.assertFalse(has_same_unit_type_as(val1, val2))
