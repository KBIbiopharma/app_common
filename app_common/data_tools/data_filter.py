from traits.api import Bool, Enum, Int, List, Str

from app_common.model_tools.data_element import DataElement

DEFAULT_MAX_ELEMENT_TO_FILTER = 500


class DataFilter(DataElement):
    """ Description of how to filter, randomize, truncate, sort, groupby a DF.

    Note that not all these operations are commutative, so they should be
    applied in the order specified by _operation_order.
    """
    #: Expression to use to filter the data (valid python passed to df.query)
    filter_expr = Str

    #: Whether to randomize entries (applied before truncation and sorting)
    randomize = Bool

    #: Max num. of elements to filter. Set to 0 to show all.
    max_num_elems = Int(DEFAULT_MAX_ELEMENT_TO_FILTER)

    #: List of possible values for the `sort_by` variable
    sort_by_values = List

    #: Column to sort the DF on
    sort_by = Enum(values="sort_by_values")

    #: Whether to sort following ascending order (True) or descending (False)
    sort_ascending = Bool(False)

    #: Name of the particle property to group the DF
    group_by = List(Str)

    #: List of group value to exclude
    group_val_black_list = List

    #: Order of DF transformation operation
    _operation_order = ["filter", "randomize", "sort", "truncate", "groupby"]
