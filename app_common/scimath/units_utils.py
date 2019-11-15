""" Utilities around unit conversion and unit management.
"""
import logging
from copy import copy
from six import string_types
import numpy as np

from scimath.units.api import convert, dimensionless, unit_parser, UnitArray, \
    UnitScalar
from scimath.units.unit import InvalidConversion

logger = logging.getLogger(__name__)

parse_unit = unit_parser.parse_unit


def unitted_list_to_array(unitted_list, target_unit=None):
    """ Returns a UnitArray given a python list of UnitScalars.
    """
    # Make a copy so modifications of the list doesn't affect the caller code:
    unitted_list = copy(unitted_list)

    if target_unit is None:
        target_unit = unitted_list[0].units
    elif isinstance(target_unit, string_types):
        target_unit = parse_unit(target_unit)

    units = [val.units for val in unitted_list]
    for i, unit in enumerate(units):
        # Test works even between a SmartUnit and a Unit
        if not units_almost_equal(unit, target_unit):
            try:
                scalar = unitted_list[i]
                unitted_list[i] = convert(float(scalar),
                                          from_unit=scalar.units,
                                          to_unit=target_unit)
            except InvalidConversion:
                all_units = [u.label for u in units]
                msg = ("Not all units equivalent: got {}".format(all_units))
                logger.exception(msg)
                raise ValueError(msg)

    return UnitArray([float(val) for val in unitted_list], units=target_unit)


def unitarray_to_unitted_list(uarr):
    """ Convert a UnitArray to a list of UnitScalars.
    """
    values = uarr.tolist()
    return [UnitScalar(val, units=uarr.units) for val in values]


def has_volume_units(units):
    if isinstance(units, (UnitScalar, UnitArray)):
        units = units.units

    return units.derivation == (3, 0, 0, 0, 0, 0, 0)


def has_mass_units(units):
    if isinstance(units, (UnitScalar, UnitArray)):
        units = units.units

    return units.derivation == (0, 1, 0, 0, 0, 0, 0)


def has_same_unit_type_as(units, tgt_units):
    """ Make sure units/UnitScalars/UnitArrays are of same types.

    By unit type, we mean, unit dimension: volume, length, mass, ... Done by
    comparing the derivation of each unit.
    """
    if isinstance(units, (UnitScalar, UnitArray)):
        units = units.units

    if isinstance(tgt_units, string_types):
        tgt_units = parse_unit(tgt_units)
    elif isinstance(tgt_units, (UnitScalar, UnitArray)):
        tgt_units = tgt_units.units

    return units.derivation == tgt_units.derivation


def unit_scalars_almost_equal(x1, x2, eps=1e-9):
    """ Returns whether 2 UnitScalars are almost equal.

    Parameters
    ----------
    x1 : UnitScalar
        First unit scalar to compare.

    x2 : UnitScalar
        Second unit scalar to compare.

    eps : float
        Absolute precision of the comparison.
    """
    if not isinstance(x1, UnitScalar):
        msg = "x1 is supposed to be a UnitScalar but a {} was passed."
        msg = msg.format(type(x1))
        logger.exception(msg)
        raise ValueError(msg)

    if not isinstance(x2, UnitScalar):
        msg = "x2 is supposed to be a UnitScalar but a {} was passed."
        msg = msg.format(type(x2))
        logger.exception(msg)
        raise ValueError(msg)

    a1 = float(x1)
    try:
        a2 = convert(float(x2), from_unit=x2.units, to_unit=x1.units)
    except InvalidConversion:
        return False
    return np.abs(a1 - a2) < eps


def units_almost_equal(unit_1, unit_2, eps=1e-9):
    """ Returns whether the units provided are almost equal.

    Implemented by comparing the unit factor, offset, derivation. If the unit
    is dimensionless, the label is also compared since dimensionless units are
    used for various custom units.

    Parameters
    ----------
    unit_1 : SmartUnit or UnitScalar or UnitArray
        First unit or unitted object to compare.

    unit_2 : SmartUnit or UnitScalar or UnitArray
        First unit or unitted object to compare.
    """
    if isinstance(unit_1, (UnitScalar, UnitArray)):
        unit_1 = unit_1.units
    if isinstance(unit_2, (UnitScalar, UnitArray)):
        unit_2 = unit_2.units

    if abs(unit_1.offset - unit_2.offset) > eps:
        return False

    if abs(unit_1.value - unit_2.value) > eps:
        return False

    if unit_1.derivation != unit_2.derivation:
        return False

    # Compare labels only for dimensionless units
    if unit_1.derivation == dimensionless.derivation:
        if unit_1.label != unit_2.label:
            return False

    return True
