""" Definition of a custom editor for a PositiveInt trait. This uses the
regular TextEditor with the approriate validation.
"""
from __future__ import print_function

from traits.api import Bool, Callable
from traitsui.api import TextEditor


def str_to_positive_int(text):
    """ Convert a string representation back to PositiveInt.
    """
    if text.strip():
        val = int(text)
        if val >= 0.:
            return int(text)
        else:
            raise ValueError("Value should be positive.")
    else:
        return 0


def positive_int_to_str(value):
    """ Convert a PositiveInt to a string representation to display
    in the text box.
    """
    if value is None:
        return ""
    else:
        return str(value)


class PositiveIntEditor(TextEditor):
    """ Edit a PositiveInt value using a TextEditor.
    """
    enter_set = Bool(True)

    auto_set = Bool(True)

    evaluate = Callable(str_to_positive_int)

    format_func = Callable(positive_int_to_str)


if __name__ == "__main__":
    from traits.api import HasTraits
    from traitsui.api import Item, View
    from app_common.traits.custom_trait_factories import PositiveInt

    class SampleModel(HasTraits):
        x = PositiveInt()
        view = View(
            Item("x", editor=PositiveIntEditor())
        )

    model = SampleModel()
    model.configure_traits()
    if model.x is None:
        print("x set to None")
    else:
        print(model.x)
