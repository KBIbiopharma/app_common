# -*- coding: utf-8 -*-
""" Utilities providing new custom assertions to support unit tests.
"""
from nose.tools import assert_false, assert_true

from app_common.traits.has_traits_utils import is_has_traits_almost_equal, \
    is_val_almost_equal


def assert_has_traits_almost_equal(obj1, obj2, eps=1e-9, ignore=(),
                                   check_type=True):
    """ Compare 2 HasTraits objects and assert they are almost equal.

    Parameters
    ----------
    obj1, obj2 : HasTraits instances
        HasTraits class instances to compare.

    eps : float
        Precision beyond which floating point values are considered different.

    ignore : sequence of str
        List of attribute names to skip from checks. These are passed
        recursively to children and must match the object's attribute name of
        one of its children attribute name.

    check_type : bool
        Check whether the 2 objects have the same type? True by default.
    """
    is_equal, msg = is_has_traits_almost_equal(
        obj1, obj2, eps=eps, ignore=ignore, check_type=check_type
    )
    error_msg = "HasTraits objects are not almost equal: {}".format(msg)
    assert_true(is_equal, error_msg)


def assert_has_traits_not_almost_equal(obj1, obj2, eps=1e-9, ignore=(),
                                       check_type=True):
    """ Compare 2 HasTraits objects and assert they are not almost equal.

    Parameters
    ----------
    obj1, obj2 : HasTraits instances
        HasTraits class instances to compare.

    eps : float
        Precision beyond which floating point values are considered different.

    ignore : sequence of str
        List of attribute names to skip from checks. These are passed
        recursively to children and must match the object's attribute name of
        one of its children attribute name.

    check_type : bool
        Check whether the 2 objects have the same type? True by default.
    """
    is_equal, msg = is_has_traits_almost_equal(
        obj1, obj2, eps=eps, ignore=ignore, check_type=check_type
    )
    error_msg = "HasTraits objects are not almost equal: {}".format(msg)
    assert_false(is_equal, error_msg)


def assert_values_almost_equal(val1, val2, eps=1e-9, ignore=()):
    """ Compare 2 objects containing HasTraits and assert they are not
    almost equal.

    Parameters
    ----------
    val1, val2 : object
        Non-HasTraits values to compare, typically attributes of a
        HasTraits class.

    attr_name : None or str [OPTIONAL]
       Name of the attribute that these values are pulled from.

    eps : float
        Precision beyond which floating point values are considered different.

    ignore : sequence of str
        List of attribute names to skip from comparisons of objects. These are
        passed recursively to elements of the values being compared and their
        children.
    """
    is_equal, msg = is_val_almost_equal(val1, val2, eps=eps, ignore=ignore)
    assert_true(is_equal, "Values are not almost equal: {}".format(msg))


def assert_values_not_almost_equal(val1, val2, eps=1e-9, ignore=()):
    """ Compare 2 objects containing HasTraits and assert they are not
    almost equal.

    Parameters
    ----------
    val1, val2 : object
        Non-HasTraits values to compare, typically attributes of a
        HasTraits class.

    attr_name : None or str [OPTIONAL]
       Name of the attribute that these values are pulled from.

    eps : float
        Precision beyond which floating point values are considered different.

    ignore : sequence of str
        List of attribute names to skip from comparisons of objects. These are
        passed recursively to elements of the values being compared and their
        children.
    """
    is_equal, msg = is_val_almost_equal(val1, val2, eps=eps, ignore=ignore)
    assert_false(is_equal, "Values are not almost equal: {}".format(msg))
