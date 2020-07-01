""" Tests for the utility functions in more_units module. """

from unittest import TestCase

from scimath.units.api import dimensionless, UnitScalar, UnitArray
from scimath.units import mass, substance

from app_common.scimath.assertion_utils import assert_unit_array_almost_equal,\
    assert_unit_scalar_almost_equal

from app_common.scimath import more_units
from app_common.scimath.units_utils import convert_units


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
