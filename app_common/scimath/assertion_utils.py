# -*- coding: utf-8 -*-
""" Utilities providing new custom assertions to support unit tests.
"""
from nose.tools import assert_false, assert_true
from numpy.testing import assert_allclose
from numpy import array, allclose

from scimath.units.api import convert

from app_common.scimath.units_utils import unit_scalars_almost_equal


def assert_unit_scalar_almost_equal(val1, val2, eps=1.e-9, msg=None):
    if msg is None:
        msg = "{} and {} are not almost equal with precision {}"
        msg = msg.format(val1, val2, eps)
    assert_true(unit_scalars_almost_equal(val1, val2, eps=eps), msg=msg)


def assert_unit_scalar_not_almost_equal(val1, val2, eps=1.e-9, msg=None):
    if msg is None:
        msg = "{} and {} unexpectedly almost equal with precision {}"
        msg = msg.format(val1, val2, eps)
    assert_false(unit_scalars_almost_equal(val1, val2, eps=eps), msg=msg)


def assert_unit_array_almost_equal(uarr1, uarr2, atol=1e-9, msg=None):
    if uarr1.units != uarr2.units:
        uarr2 = convert(uarr2, uarr2.units, uarr1.units)

    if msg is None:
        msg = "{} and {} are not almost equal with precision {}"
        msg = msg.format(uarr1, uarr2, atol)
    assert_allclose(array(uarr2), array(uarr1), atol=atol, err_msg=msg)


def assert_unit_array_not_almost_equal(uarr1, uarr2, atol=1e-9, msg=None):
    if uarr1.units != uarr2.units:
        uarr2 = convert(uarr2, uarr2.units, uarr1.units)

    if msg is None:
        msg = "{} and {} are almost equal with precision {}"
        msg = msg.format(uarr1, uarr2, atol)
    assert_false(allclose(array(uarr2), array(uarr1), atol=atol), msg=msg)
