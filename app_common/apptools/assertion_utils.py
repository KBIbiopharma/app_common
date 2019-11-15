from nose.tools import assert_equal

from scimath.units.api import UnitArray, UnitScalar
from app_common.scimath.assertion_utils import assert_unit_array_almost_equal,\
    assert_unit_scalar_almost_equal


def flexible_assert_equal(x1, x2, **kw):
    """ Flexible assertion equality
    """
    if isinstance(x1, UnitArray):
        assert_unit_array_almost_equal(x1, x2, **kw)
    elif isinstance(x1, UnitScalar):
        assert_unit_scalar_almost_equal(x1, x2, **kw)
    else:
        assert_equal(x1, x2, **kw)
