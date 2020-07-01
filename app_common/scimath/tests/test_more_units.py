""" Tests for the utility functions in more_units module. """

from unittest import TestCase
from numpy.testing import assert_allclose

from scimath.units.api import dimensionless, UnitScalar, UnitArray
from scimath.units.unit import InvalidConversion
from scimath.units import mass, substance

from app_common.scimath.assertion_utils import assert_unit_array_almost_equal,\
    assert_unit_scalar_almost_equal

from app_common.scimath import more_units
from app_common.scimath.more_units import convert_units


class TestConvertUnits(TestCase):

    # Tests -------------------------------------------------------------------

    def test_scalar_convert_units(self):
        scalar_data = UnitScalar(1, units=more_units.length.m)
        conv_data = convert_units(scalar_data, more_units.length.cm)
        self.assertEqual(conv_data, UnitScalar(100, units=more_units.length.cm))

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


class TestVolumeUnits(TestCase):

    # Tests -------------------------------------------------------------------

    def test_column_volume(self):
        vol = UnitScalar(1, units=more_units.column_volumes)
        self.assertIsInstance(vol, UnitScalar)
        unit = more_units.column_volumes
        # It's dimensionless since it's a ratio of volumes:
        self.assertEqual(unit.derivation, dimensionless.derivation)
        self.assertEqual(unit.label, "CV")

    def test_parse_column_volume_label(self):
        vol = UnitScalar(1, units="CV")
        vol2 = UnitScalar(1, units=more_units.column_volumes)
        assert_unit_scalar_almost_equal(vol, vol2)

    def test_g_per_liter_resin(self):
        vol = UnitScalar(1, units=more_units.g_per_liter_resin)
        self.assertIsInstance(vol, UnitScalar)

        # It's dimensionless since custom and dimensions meaningless:
        unit = more_units.g_per_liter_resin
        self.assertEqual(unit.derivation, dimensionless.derivation)
        self.assertIn("g", unit.label)
        self.assertIn("L", unit.label)
        self.assertIn("resin", unit.label)

    def test_parse_g_per_liter_resin_label(self):
        vol = UnitScalar(1, units="g/Liter_resin")
        vol2 = UnitScalar(1, units=more_units.g_per_liter_resin)
        assert_unit_scalar_almost_equal(vol, vol2)

    def test_g_per_liter_resin_to_cv(self):
        concentration = UnitScalar(8.03, units="g/L")
        vol = UnitScalar(0.0635, units=more_units.g_per_liter_resin)
        # without a concentration, the conversion is impossible:
        with self.assertRaises(ValueError):
            convert_units(vol, tgt_unit="CV")

        new_vol = convert_units(vol, tgt_unit="CV",
                                concentration=concentration)
        expected = UnitScalar(0.0635 / 8.03, units="CV")
        assert_unit_scalar_almost_equal(new_vol, expected)

    def test_g_per_liter_resin_to_cv_conc_units(self):
        """ g/L_resin -> CV, passing concentration in different unit.
        """
        concentration = UnitScalar(8030, units="g/m**3")
        vol = UnitScalar(0.0635, units=more_units.g_per_liter_resin)
        expected = UnitScalar(0.0635/8.03, units="CV")
        new_vol = convert_units(vol, tgt_unit="CV",
                                concentration=concentration)
        assert_unit_scalar_almost_equal(new_vol, expected)

    def test_cv_to_g_per_liter_resin(self):
        concentration = UnitScalar(8.03, units="g/L")
        # 0.0635/8.03
        vol = UnitScalar(0.007907845579078457, units="CV")
        # without a concentration, the conversion is impossible:
        with self.assertRaises(ValueError):
            convert_units(vol, tgt_unit=more_units.g_per_liter_resin)

        expected = UnitScalar(0.0635, units=more_units.g_per_liter_resin)
        new_vol = convert_units(vol, tgt_unit=more_units.g_per_liter_resin,
                                concentration=concentration)
        assert_unit_scalar_almost_equal(new_vol, expected)


class TestAbsorptionUnit(TestCase):
    def test_au_to_milli_au(self):
        x = UnitArray([1, 2, 3], units=more_units.absorption_unit)
        conv_data = convert_units(x, more_units.milli_absorption_unit)
        expected = UnitArray([1000, 2000, 3000],
                             units=more_units.milli_absorption_unit)
        assert_unit_array_almost_equal(conv_data, expected)

    def test_milli_au_to_au(self):
        x = UnitArray([1000, 2000, 3000],
                      units=more_units.milli_absorption_unit)
        conv_data = convert_units(x, more_units.absorption_unit)
        expected = UnitArray([1, 2, 3], units=more_units.absorption_unit)
        assert_unit_array_almost_equal(conv_data, expected)


class TestMolecularWeightUnits(TestCase):
    def test_gram_per_mol(self):
        x = UnitArray([1000, 2000, 3000], units=more_units.gram_per_mol)
        expected = UnitArray([1000, 2000, 3000], units=mass.g / substance.mole)
        assert_unit_array_almost_equal(x, expected)

        y = UnitArray([1000, 2000, 3000], units="g/mol")
        assert_unit_array_almost_equal(y, expected)

    def test_gram_per_mol_to_kilo_per_mol(self):
        x = UnitArray([1000, 2000, 3000], units=more_units.gram_per_mol)
        expected = UnitArray([1, 2, 3], units=more_units.kilogram_per_mol)
        assert_unit_array_almost_equal(x, expected)

    def test_gram_per_mol_to_kilo_per_mol_str(self):
        y = UnitArray([1000, 2000, 3000], units="g/mol")
        expected = UnitArray([1, 2, 3], units="kg/mol")
        assert_unit_array_almost_equal(y, expected)

    def test_dalton(self):
        x = UnitArray([1000, 2000, 3000], units=more_units.gram_per_mol)
        expected = UnitArray([1000, 2000, 3000], units=more_units.dalton)
        assert_unit_array_almost_equal(x, expected)
        # This unit is equal but distinct:
        self.assertIsNot(more_units.dalton, more_units.gram_per_mol)

        y = UnitArray([1000, 2000, 3000], units="Da")
        assert_unit_array_almost_equal(y, expected)

    def test_kilo_dalton(self):
        x = UnitArray([1, 2, 3], units=more_units.kilo_dalton)
        expected = UnitArray([1, 2, 3], units=more_units.kilogram_per_mol)
        assert_unit_array_almost_equal(x, expected)
        # This unit is equal but distinct:
        self.assertIsNot(more_units.kilo_dalton, more_units.kilogram_per_mol)

        y = UnitArray([1, 2, 3], units="kDa")
        assert_unit_array_almost_equal(y, expected)

    def test_dalton_to_kilo_dalton(self):
        x = UnitArray([1000, 2000, 3000], units=more_units.dalton)
        expected = UnitArray([1, 2, 3], units=more_units.kilo_dalton)
        assert_unit_array_almost_equal(x, expected)

    def test_dalton_to_kilo_dalton_str(self):
        y = UnitArray([1000, 2000, 3000], units="Da")
        expected = UnitArray([1, 2, 3], units="kDa")
        assert_unit_array_almost_equal(y, expected)
