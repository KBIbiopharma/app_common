""" Definition of a custom editor for a PositiveFloat trait. This uses the
regular TextEditor with the appropriate validation.
"""
from __future__ import print_function

from traits.api import Bool, Callable
from traitsui.api import TextEditor


def str_to_positive_float(text):
    """ Convert a string representation back to PositiveFloat.
    """
    if text.strip():
        val = float(text)
        if val >= 0.:
            return float(text)
        else:
            raise ValueError("Value should be positive.")
    else:
        return 0.0


def positive_float_to_str(value):
    """ Convert a PositiveFloat to a string representation to display
    in the text box.
    """
    if value is None:
        return ""
    else:
        return str(value)


class PositiveFloatEditor(TextEditor):
    """ Edit a PositiveFloat value using a TextEditor.
    """
    enter_set = Bool(True)

    auto_set = Bool(True)

    evaluate = Callable(str_to_positive_float)

    format_func = Callable(positive_float_to_str)


if __name__ == "__main__":
    from traits.api import HasTraits
    from traitsui.api import Item, View
    from app_common.traits.custom_trait_factories import PositiveFloat

    class SampleModel(HasTraits):
        x = PositiveFloat()
        view = View(
            Item("x", editor=PositiveFloatEditor())
        )

    model = SampleModel()
    model.configure_traits()
    if model.x is None:
        print("x set to None")
    else:
        print(model.x)
