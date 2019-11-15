import sys

import numpy as np

from traits.api import Array, Float, Instance, Int, Range, Str, Trait, \
    TraitError
try:
    from scimath.units.unit_scalar import UnitArray, UnitScalar
    scimath_imported = True
except ImportError:
    scimath_imported = False


# -----------------------------------------------------------------------------
# Trait factories
# -----------------------------------------------------------------------------


def key_trait_factory(trait_type=None):
    """ Creates a key trait.

    Key traits are traits with metadata annotations that identify the trait to
    be a special trait. The intention is that other tools that inspect an
    object and treat these differently from normal traits.

    One particular usecase here is for grouping/filtering collections of
    objects based on the key trait.
    """
    if trait_type is None:
        trait_type = Str

    default = trait_type.default_value
    trait = Trait(default, trait_type, is_key=True)
    return trait


Key = key_trait_factory


def parameter_trait_factory(default=None, trait_type=None):
    """ Creates a parameter trait.

    Parameter traits are essentially standard traits of type `data_type`
    with metadata annotations specfic to parameters (e.g. units).

    One particular use-case here is to figure out the attributes of interest
    when performing a parameter sweep.
    """
    if trait_type is None:
        trait_type = Instance(UnitScalar)

    return Trait(default, trait_type, is_parameter=True)


if scimath_imported:
    Parameter = parameter_trait_factory(trait_type=Instance(UnitScalar))

if scimath_imported:
    ParameterUnitArray = parameter_trait_factory(
        trait_type=Instance(UnitArray)
    )

ParameterArray = parameter_trait_factory(trait_type=Array)

ParameterInt = parameter_trait_factory(trait_type=Int)

ParameterFloat = parameter_trait_factory(trait_type=Float)


def _positive_integer(value=0, **kwargs):
    """ Creates a positive integer trait

    Positive traits are standard traits of type Range with value int >= 0

    General use case is for limiting acceptable values to the positive domain
    """
    if not isinstance(value, int):
        msg = 'Invalid default value. Expected integer but received type: {!r}'
        msg = msg.format(type(value))
        raise TraitError(msg)

    return Range(low=0, high=sys.maxint, value=value, **kwargs)


PositiveInt = _positive_integer


def _positive_integer_parameter(value=0, **kwargs):
    kwargs["is_parameter"] = True
    return _positive_integer(value=value, **kwargs)


PositiveIntParameter = _positive_integer_parameter


def _positive_float(value=0.0, **kwargs):
    """ Creates a positive float trait

    Positive traits are standard traits of type Range with value float >= 0

    General usecase is for limiting acceptable values to the positive domain
    """
    return Range(low=0.0, high=np.inf, value=float(value), **kwargs)


PositiveFloat = _positive_float


def _positive_float_parameter(value=0.0, **kwargs):
    kwargs["is_parameter"] = True
    return _positive_float(value=value, **kwargs)


PositiveFloatParameter = _positive_float_parameter
