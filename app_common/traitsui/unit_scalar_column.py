from traits.api import Bool, Callable
from traitsui.table_column import ObjectColumn

from .unit_scalar_editor import str_to_unit_scalar, UnitScalarEditor, \
    unit_scalar_to_str


class UnitScalarColumn(ObjectColumn):
    """ A special Column defined to control how a UnitScalar is displayed when
    the cell it not double-clicked. Otherwise the unit isn't showed.
    """
    format_func = Callable(unit_scalar_to_str)

    editor = UnitScalarEditor()

    editable = Bool(True)

    auto_editable = Bool(True)

    def set_value(self, value):
        return str_to_unit_scalar(value)
