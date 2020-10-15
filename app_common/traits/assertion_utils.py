# -*- coding: utf-8 -*-
""" Utilities providing new custom assertions to support unit tests.
"""
from nose.tools import assert_false, assert_true

from app_common.traits.has_traits_utils import is_has_traits_almost_equal, \
    is_val_almost_equal


def assert_has_traits_almost_equal(obj1, obj2, **kwargs):
    """ Compare 2 HasTraits objects and assert they are almost equal.

    Parameters
    ----------
    obj1, obj2 : HasTraits instances
        HasTraits class instances to compare.

    kwargs : dict
        Additional keyword arguments passed to `is_has_traits_almost_equal`.
    """
    is_equal, msg = is_has_traits_almost_equal(obj1, obj2, **kwargs)
    error_msg = f"HasTraits objects are not almost equal: {msg}"
    assert_true(is_equal, error_msg)


def assert_has_traits_not_almost_equal(obj1, obj2, **kwargs):
    """ Compare 2 HasTraits objects and assert they are not almost equal.

    Parameters
    ----------
    obj1, obj2 : HasTraits instances
        HasTraits class instances to compare.

    kwargs : dict
        Additional keyword arguments passed to `is_has_traits_almost_equal`.

    """
    is_equal, msg = is_has_traits_almost_equal(obj1, obj2, **kwargs)
    error_msg = f"HasTraits objects are unexpectedly almost equal: {msg}"
    assert_false(is_equal, error_msg)


def assert_values_almost_equal(val1, val2, **kwargs):
    """ Compare 2 objects containing HasTraits and assert they are not
    almost equal.

    Parameters
    ----------
    val1, val2 : object
        Non-HasTraits values to compare, typically attributes of a
        HasTraits class.

    kwargs : dict
        Additional keyword arguments passed to `is_val_almost_equal`.
    """
    is_equal, msg = is_val_almost_equal(val1, val2, **kwargs)
    assert_true(is_equal, f"Values are not almost equal: {msg}")


def assert_values_not_almost_equal(val1, val2, **kwargs):
    """ Compare 2 objects containing HasTraits and assert they are not
    almost equal.

    Parameters
    ----------
    val1, val2 : object
        Non-HasTraits values to compare, typically attributes of a
        HasTraits class.

    kwargs : dict
        Additional keyword arguments passed to `is_val_almost_equal`.
    """
    is_equal, msg = is_val_almost_equal(val1, val2, **kwargs)
    assert_false(is_equal, f"Values are unexpectedly almost equal: {msg}")
