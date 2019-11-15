
import logging
import numpy as np
import pandas as pd
from six import PY2, string_types

from traits.api import HasTraits
from scimath.units.api import UnitScalar
from traits.trait_handlers import TraitListObject, TraitDictObject

from app_common.model_tools.data_element import DataElement

if PY2:
    from types import TypeType
else:
    TypeType = type

logger = logging.getLogger(__name__)

POTENTIAL_PARAMETER_TYPES = (int, float, np.ndarray, pd.Series)


def search_parameters_in_data(data_obj, attr_path="", exclude=(),
                              data_klass=DataElement):
    """ Build a list of paths to Parameter type traits found in a Data obj.

    Parameters
    ----------
    data_obj : ChromatographyData
        Data object searched for Parameter type attribute.

    attr_path : str
        Attribute path to prepend to the attributes found. (Needed since
        function is recursive. shouldn't be needed by users).

    exclude : tuple of strings
        List of attribute names of the data_obj that should be ignored.

    data_klass : type
        Type of objects that are to be searched into. Regular HasTraits objects
        are skipped.

    TODO: Add support for excluding extended attribute path.

    TODO: Add support for having 2 versions of the attribute path: an eval-able
    one (which is what is currently returned) and a user friendly one. The
    friendly one should be highly customizable because will be very problem
    dependent, might even be user dependent.
    """
    parameter_list = []

    for attr_name, attr_val in data_obj.__dict__.items():
        if attr_name.startswith("_") or attr_name in exclude:
            continue

        if attr_path:
            absolute_attr_path = ".".join([attr_path, attr_name])
        else:
            absolute_attr_path = attr_name

        if isinstance(attr_val, data_klass):
            parameter_list += search_parameters_in_data(
                attr_val, attr_path=absolute_attr_path
            )
        elif isinstance(attr_val, (list, tuple, TraitListObject)):
            parameter_list += search_parameters_in_sequence(
                attr_val, attr_path=absolute_attr_path
            )
        elif isinstance(attr_val, (dict, TraitDictObject)):
            parameter_list += search_parameters_in_dict(
                attr_val, attr_path=absolute_attr_path
            )
        elif isinstance(attr_val, (HasTraits, string_types)):
            continue
        elif isinstance(attr_val, POTENTIAL_PARAMETER_TYPES):
            trait = data_obj.trait(attr_name)
            if trait.is_parameter:
                parameter_list += _expand_attr_name(absolute_attr_path,
                                                    attr_val)
        else:
            # Types there is nothing to do with.
            pass

    return parameter_list


def search_parameters_in_sequence(seq, attr_path=""):
    """ Walk a list/tuple to look for and report the path of Parameter objects.
    """
    type_supported = (list, tuple, pd.Series)
    if not isinstance(seq, type_supported):
        msg = "search_parameters_in_sequence only supports {} but received {}"
        msg = msg.format(type_supported, type(seq))
        raise ValueError(msg)

    param_list = []

    for i, val in enumerate(seq):
        param_list += search_parameters_in_collection_value(
            i, val, attr_path=attr_path
        )

    return param_list


def search_parameters_in_dict(dict_obj, attr_path=""):
    """ Walk a dictionary to look for and report the path of Parameter objects.
    """
    param_list = []

    for key, val in dict_obj.items():
        # Make the key have quotes so that the resulting entry can be eval-ed
        key = "'{}'".format(key)
        param_list += search_parameters_in_collection_value(
            key, val, attr_path=attr_path
        )

    return param_list


def search_parameters_in_collection_value(item_id, item, attr_path=""):
    """ Return the Parameter content of a single object in a collection.

    This can be used to search for the parameter content of a list, dict,
    tuple, series, dataframe and anything that can contain complex values and
    have a unique identification used by the __getitem__.
    """
    if isinstance(item, (string_types, TypeType)):
        return []
    elif isinstance(item, POTENTIAL_PARAMETER_TYPES):
        return []
    elif isinstance(item, DataElement):
        attr_path += "[{}]".format(item_id)
        parameter_list = search_parameters_in_data(item, attr_path=attr_path)
    elif isinstance(item, (list, tuple, TraitListObject)):
        attr_path += "[{}]".format(item_id)
        parameter_list = search_parameters_in_sequence(
            item, attr_path=attr_path
        )
    elif isinstance(item, (dict, TraitDictObject)):
        attr_path += "[{}]".format(item_id)
        parameter_list = search_parameters_in_dict(
            item, attr_path=attr_path
        )
    else:
        msg = ("Failed to handle an element of {}: not implemented to deal "
               "with {} (type {}).".format(attr_path, item, type(item)))
        logger.exception(msg)
        raise ValueError(msg)

    return parameter_list


def _expand_attr_name(attr_path, attr_val):
    """ Convert attr_path into sub-attribute paths based on the parameter.

    An attribute path might be expanded into a list of attributes that can be
    scanned individually during a grid search. For example, an 4 element-array
    named 'foo.bar' will be expanded into:
        ['foo.bar[0]', 'foo.bar[1]', 'foo.bar[2]', 'foo.bar[3]'].
    """
    if isinstance(attr_val, (int, float, UnitScalar)):
        return [attr_path]
    elif isinstance(attr_val, (np.ndarray)):
        return [attr_path + "[{}]".format(i) for i in range(len(attr_val))]
    elif isinstance(attr_val, (pd.Series)):
        return [attr_path + "[{}]".format(ind) for ind in attr_val.index]
    else:
        msg = "Don't know how to expand {}".format(type(attr_path))
        logger.debug(msg)
        raise NotImplementedError(msg)
