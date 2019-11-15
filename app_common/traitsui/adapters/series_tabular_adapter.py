""" Tabular adapter for a Pandas series.
"""
import numpy as np
import pandas as pd

from traits.api import Any, Bool, Color, Enum, HasTraits, Instance, Property, \
    Str
from traitsui.api import View, Item, TabularEditor
from traitsui.tabular_adapter import TabularAdapter


class PandasSeriesAdapter(TabularAdapter):
    """ Generic tabular adapter for Pandas series.

    The logic of the adapter is to store in the item attribute a row in the
    table. Then methods testing if
    """

    index_color = Color("lightgrey")

    index_label = Str("Index")

    values_label = Str("Values")

    index_tooltip = Str

    values_tooltip = Str

    # Can the text value of each item be edited:
    # Note: Qt4 only. The WX widget doesn't support treating different columns
    # differently.
    can_edit_index = Bool(False)

    # Can the text value of each item be edited:
    # Note: Qt4 only. The WX widget doesn't support treating different columns
    # differently.
    can_edit_values = Bool(True)

    # Current item (row) being adapted:
    item = Any

    #: The text to use for a generic entry.
    text = Property

    #: The alignment for each cell
    alignment = Property(Enum('left', 'center', 'right'))

    #: The text to use for a row index.
    index_text = Property

    #: The alignment to use for a row index.
    index_alignment = Property

    def _get_index_alignment(self):
        index = getattr(self.object, self.name).index
        if np.issubdtype(index.dtype, np.number):
            return 'right'
        else:
            return 'left'

    def _get_alignment(self):
        if self.column_id == 'index':
            column = self.item.index
        else:
            column = self.item

        if np.issubdtype(column.dtype, np.number):
            return 'right'
        else:
            return 'left'

    def _get_content(self):
        return self.item.iloc[0]

    def _get_text(self):
        format = self.get_format(self.object, self.name, self.row, self.column)
        return format % self.get_content(self.object, self.name, self.row,
                                         self.column)

    def _set_text(self, value):
        if not self.can_edit_values:
            return

        self.item.iloc[0] = value

    def _get_index_text(self):
        return str(self.item.index[0])

    def _set_index_text(self, value):
        if not self.can_edit_index:
            return

        index = getattr(self.object, self.name).index
        index[self.row] = value

    def _columns_default(self):
        """ List of (column labels, column_id)s used to extract values.
        """
        return [(self.index_label, 'index'), (self.values_label, 'value')]

    def get_item(self, object, trait, row):
        """ Collect 1 row of the Series. """
        return getattr(object, trait).iloc[row:row+1]

    def get_can_edit(self, object, trait, row, column):
        """ Returns whether the user can edit a specified
        *object.trait[row]* item.
        """
        return self.can_edit_index or self.can_edit_values

    def get_can_edit_cell(self, object, trait, row, column):
        """ Returns whether the user can edit a specified
        *object.trait[row, column]* cell.
        """
        if column == 0:
            return self.can_edit_index
        else:
            return self.can_edit_values

    def get_bg_color(self, object, trait, row, column):
        """ Returns the background color for a specified *object.trait[row]*
        item. A result of None means use the default background color.
        """
        if column == 0:
            return self.index_color
        else:
            return None

    def get_tooltip(self, object, trait, row, column):
        """ Returns the tooltip for a specified row.
        """
        if column == 0:
            return self.values_tooltip
        else:
            return self.index_tooltip


if __name__ == "__main__":

    class ShowSeries(HasTraits):

        data = Instance(pd.Series)

        view = View(
            Item(
                'data',
                editor=TabularEditor(
                    adapter=PandasSeriesAdapter()
                ),
                show_label=False),
            title='Series Viewer',
            width=0.3,
            height=0.8,
            resizable=True,
        )

    demo = ShowSeries(data=pd.Series([1, 2, 3, 4, 5], index=list("abcde")))
    demo.configure_traits()
