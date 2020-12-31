from nose.tools import assert_equal
from pandas.testing import assert_frame_equal, assert_series_equal


def assert_frame_not_equal(*args, **kwargs):
    """ Not implemented in pandas."""
    try:
        assert_frame_equal(*args, **kwargs)
    except AssertionError:
        # frames are not equal
        pass
    else:
        # frames are equal
        raise AssertionError


def assert_series_not_equal(*args, **kwargs):
    """ Not implemented in pandas."""
    try:
        assert_series_equal(*args, **kwargs)
    except AssertionError:
        # Series are not equal
        pass
    else:
        # Series are equal
        raise AssertionError


def flexible_assert_equal(x1, x2, **kw):
    """ Flexible assertion equality, including support for scimath objects.
    """
    from scimath.units.api import UnitArray, UnitScalar
    from app_common.scimath.assertion_utils import \
        assert_unit_array_almost_equal, \
        assert_unit_scalar_almost_equal

    if isinstance(x1, UnitArray):
        assert_unit_array_almost_equal(x1, x2, **kw)
    elif isinstance(x1, UnitScalar):
        assert_unit_scalar_almost_equal(x1, x2, **kw)
    else:
        assert_equal(x1, x2, **kw)
