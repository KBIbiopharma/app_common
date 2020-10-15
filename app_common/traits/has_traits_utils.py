import logging
import numpy as np
import pandas as pd
from types import BuiltinFunctionType, BuiltinMethodType, \
    FunctionType, MethodType, ModuleType

from traits.api import HasTraits
try:
    from scimath.units.api import UnitArray, UnitScalar
    scimath_imported = True
except ImportError:
    scimath_imported = False

from traits.trait_handlers import TraitListObject, TraitDictObject

logger = logging.getLogger(__name__)

POTENTIAL_PARAMETER_TYPES = (int, float, np.ndarray, pd.Series)

TRAITS_PROPERTY_CACHE_PREFIX = "_traits_cache_"

IGNORE_TYPES = (BuiltinFunctionType, BuiltinMethodType, FunctionType,
                MethodType, ModuleType)


def is_has_traits_almost_equal(obj1, obj2, attr_name="", eps=1e-9, ignore=(),
                               check_type=True, check_dtype=False,
                               debug=False):
    """ Test if 2 traits objects are almost equal up to a certain precision.

    Parameters
    ----------
    obj1, obj2 : HasTraits instances
        HasTraits class instances to compare.

    attr_name : str
        Object path to obj1 and obj2. Used for reporting only since this
        function is recursive.

    eps : float
        Precision beyond which floating point values are considered different.

    ignore : sequence of str
        List of attribute names to skip from checks. These are passed
        recursively to children and must match the object's attribute name of
        one of its children attribute name.

    check_type : bool
        Check whether the 2 objects have the same type? True by default.

    check_dtype : bool
        Whether to check the dtypes of the numpy array attributes.

    debug : bool
        Whether to print attribute paths during usage. Useful to watch the
        execution of the comparison, for debugging or timing purposes.
    """
    if not isinstance(obj1, HasTraits):
        msg = "First arg ({}) not a HasTraits class: {}"
        return False, msg.format(attr_name, obj1)

    if not isinstance(obj2, HasTraits):
        msg = "Second arg ({}) not a HasTraits class: {}"
        return False, msg.format(attr_name, obj2)

    if check_type:
        if obj1.__class__ != obj2.__class__:
            type1 = obj1.__class__.__name__
            type2 = obj2.__class__.__name__
            return False, "Different types ({} vs {})".format(type1, type2)

    trait_names_to_ignore = set(ignore)

    obj1_traits = set(obj1.trait_names())
    obj2_traits = set(obj2.trait_names())
    # Make sure the 2 objects don't differ by more than the Traits cache
    # attributes
    for trait_name in obj1_traits ^ obj2_traits:
        if not trait_name.startswith(TRAITS_PROPERTY_CACHE_PREFIX) and \
                        trait_name not in trait_names_to_ignore:
            if attr_name:
                ext_trait_name = attr_name + "." + trait_name
            else:
                ext_trait_name = trait_name

            return False, "Different trait content: {}".format(ext_trait_name)

    for trait, val1 in trait_dict(obj1).items():
        if trait in trait_names_to_ignore:
            continue
        try:
            val2 = getattr(obj2, trait)
        except AttributeError:
            return False, "Trait {} present in obj1 but not obj2".format(trait)

        if attr_name:
            trait_path = attr_name + "." + trait
        else:
            trait_path = trait

        if debug:
            print(f"Comparing objects' {trait_path} attribute.")

        if isinstance(val1, HasTraits):
            equal, msg = is_has_traits_almost_equal(
                val1, val2, trait_path, eps=eps, ignore=ignore, debug=debug
            )
        else:
            equal, msg = is_val_almost_equal(
                val1, val2, trait_path, eps=eps, check_dtype=check_dtype,
                ignore=ignore, debug=debug
            )
        if not equal:
            return False, msg

    return True, ""


def is_val_almost_equal(val1, val2, attr_name="", check_dtype=False, eps=1e-9,
                        ignore=(), debug=False):
    """ Test if 2 values are almost equal up to a certain precision.

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

    check_dtype : bool
        Whether to check the dtypes if the values are numpy arrays.

    debug : bool
        Whether to print attribute paths during usage. Useful to watch the
        execution of the comparison, for debugging or timing purposes.
    """
    if attr_name is None:
        if hasattr(val1, "name"):
            attr_name = val1.name
        else:
            attr_name = ""

    if type(val1) != type(val2):
        # Don't raise an exception because it could be a float and an int,
        # which are considered almost equal.
        msg = "val1 and val2 are of different types: {} is {} and {} is {}"
        msg = msg.format(val1, type(val1), val2, type(val2))
        logger.debug(msg)

    if isinstance(val1, (int, str, set)):
        if val1 != val2:
            return False, build_message(attr_name, val1, val2)
    elif val1 is None or val2 is None:
        if val1 is not val2:
            return False, build_message(attr_name, val1, val2)
    elif isinstance(val1, float):
        if np.abs(val1 - val2) > eps:
            return False, build_message(attr_name, val1, val2)
    elif scimath_imported and isinstance(val1, UnitScalar):
        # FIXME: add support different units
        different_unit = val1.units != val2.units
        different_values = np.abs(val1.tolist() - val2.tolist()) > eps
        if different_unit or different_values:
            return False, build_message(attr_name, val1, val2)
    elif scimath_imported and isinstance(val1, UnitArray):
        # FIXME: add support different units
        different_units = val1.units != val2.units
        if different_units:
            return False, build_message(attr_name, val1, val2, "(units)")
        bare_val1 = np.array(val1.tolist())
        bare_val2 = np.array(val2.tolist())
        different_values = (np.abs(bare_val1 - bare_val2) > eps)
        if np.any(different_values):
            return False, build_message(attr_name, val1, val2, "(values)")
    elif isinstance(val1, np.ndarray):
        if val1.shape != val2.shape:
            return False, build_message(attr_name, val1, val2, "(shape)")
        if check_dtype:
            if val1.dtype != val2.dtype:
                return False, build_message(attr_name, val1, val2, "(dtype)")
        if np.issubdtype(val1.dtype, np.character):
            # ndarray of string, bytes or unicode
            # Convert to same dtype so element by element equality can be
            # checked:
            val2 = val2.astype(val1.dtype)
        if np.issubdtype(val1.dtype, np.character):
            # ndarray is a string or unicode
            if val1.size != sum(val1 == val2):
                return False, build_message(attr_name, val1, val2, "(values)")
        elif np.any(np.abs(val1 - val2) > eps):
            return False, build_message(attr_name, val1, val2, "(values)")
    elif isinstance(val1, (list, tuple, TraitListObject)):
        if len(val1) != len(val2):
            return False, build_message(attr_name, val1, val2, "(length)")
        for i, (el1, el2) in enumerate(zip(val1, val2)):
            subattr_name = "{}[{}]".format(attr_name, i)
            if isinstance(el1, HasTraits):
                equal, msg = is_has_traits_almost_equal(
                    el1, el2, attr_name=subattr_name, eps=eps, ignore=ignore,
                    debug=debug
                )
                if not equal:
                    return False, msg
            else:
                equal, msg = is_val_almost_equal(
                    el1, el2, attr_name=subattr_name, eps=eps, ignore=ignore
                )
                if not equal:
                    return False, msg
    elif isinstance(val1, (dict, TraitDictObject)):
        if set(val1.keys()) != set(val2.keys()):
            return False, build_message(attr_name, val1, val2, "(keys)")
        for key in val1:
            el1 = val1[key]
            el2 = val2[key]
            val = "{}[{}]".format(attr_name, key)
            if isinstance(el1, HasTraits):
                equal, msg = is_has_traits_almost_equal(
                    el1, el2, attr_name=val, eps=eps, ignore=ignore,
                    debug=debug
                )
                if not equal:
                    return False, msg
            else:
                equal, msg = is_val_almost_equal(el1, el2, attr_name=val,
                                                 eps=eps, ignore=ignore)
                if not equal:
                    return False, msg
    elif isinstance(val1, pd.Series):
        name = "{}.index".format(attr_name)
        equal, msg = is_val_almost_equal(
            val1.index, val2.index, attr_name=name, eps=eps, ignore=ignore
        )
        if not equal:
            return False, msg

        name = "{}.values".format(attr_name)
        equal, msg = is_val_almost_equal(
            list(val1), list(val2), attr_name=name, eps=eps, ignore=ignore
        )
        if not equal:
            return False, msg
    elif isinstance(val1, pd.DataFrame):
        name = "{}.index".format(attr_name)
        equal, msg = is_val_almost_equal(
            val1.index, val2.index, attr_name=name, eps=eps, ignore=ignore
        )
        if not equal:
            return False, msg

        name = "{}.columns".format(attr_name)
        equal, msg = is_val_almost_equal(
            set(val1.columns), set(val2.columns), attr_name=name, eps=eps,
            ignore=ignore
        )
        if not equal:
            return False, msg

        for series_name in val1:
            name = "{}.{}".format(attr_name, series_name)
            equal, msg = is_val_almost_equal(
                val1[series_name], val2[series_name], attr_name=name, eps=eps,
                ignore=ignore
            )
            if not equal:
                return False, msg
    elif isinstance(val1, pd.core.index.Index):
        equal, msg = is_val_almost_equal(
            list(val1), list(val2), attr_name=attr_name, eps=eps, ignore=ignore
        )
        if not equal:
            return False, msg
    elif isinstance(val1, type):
        equal = val1 is val2
        if not equal:
            return False, build_message(attr_name, val1, val2)
    elif isinstance(val1, IGNORE_TYPES):
        return True, ""
    else:
        # This is a pure python object: loop through its attributes:
        try:
            if not hasattr(val1, "__dict__"):
                return True, ""

            ignore = set(ignore)
            for subattr_name, attr1 in val1.__dict__.items():
                if subattr_name in ignore:
                    continue

                attr2 = getattr(val2, subattr_name)
                val = "{}.{}".format(attr_name, subattr_name)
                if isinstance(attr1, HasTraits):
                    equal, msg = is_has_traits_almost_equal(
                        attr1, attr2, attr_name=val, eps=eps, ignore=ignore
                    )
                else:
                    equal, msg = is_val_almost_equal(
                        attr1, attr2, attr_name=val, eps=eps, ignore=ignore
                    )
                if not equal:
                    return False, msg

        except Exception as e:
            msg = ("Unsupported attribute type: {} is a {}. Comparison lead "
                   "the the following error: {}")
            msg = msg.format(attr_name, type(val1), e)
            logger.exception(msg)
            raise ValueError(msg)

    return True, ""


def trait_dict(trait_obj, include_properties=False):
    """ This creates a dictionary of attributes similar to __dict__, but skips
    listeners, events and optionally properties.
    """
    trait_dict = {}
    for trait in trait_obj.trait_names():
        if include_properties:
            skip_trait = (trait.startswith("trait_") or
                          is_trait_event(trait_obj, trait))
        else:
            skip_trait = (trait.startswith("trait_") or
                          is_trait_event(trait_obj, trait) or
                          is_trait_property(trait_obj, trait))

        if skip_trait:
            continue

        trait_dict[trait] = getattr(trait_obj, trait)
    return trait_dict


def is_trait_property(has_trait_obj, trait_name):
    return has_trait_obj.trait(trait_name).type == "property"


def is_trait_event(has_trait_obj, trait_name):
    return has_trait_obj.trait(trait_name).type == "event"


def is_trait_constant(has_trait_obj, trait_name):
    return has_trait_obj.trait(trait_name).type == "constant"


def get_trait_type(has_trait_obj, trait_name):
    return has_trait_obj.trait(trait_name).type


def build_message(attr_name, val1, val2, details=""):
    """ Build error message for is_has_traits_almost_equal and
    is_val_almost_equal to return.
    """
    type1 = type(val1)
    type2 = type(val2)
    msg = "Different {} {}. Types: {} vs {}. Values: \n{} \nvs \n{}"
    msg = msg.format(attr_name, details, type1, type2, repr(val1), repr(val2))
    return msg
