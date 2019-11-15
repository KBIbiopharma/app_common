""" Definition of a custom editor for a UnitScalar instance. This uses the
regular textEditor with the approriate validation to go back and forth between
the unitscalar object and the text representation.
"""
from __future__ import print_function

import logging

from traitsui.api import TextEditor
from scimath.units.api import dimensionless, UnitScalar


logger = logging.getLogger(__name__)


def str_to_unit_scalar(text):
    """ Convert a string representation back to an instance of a UnitScalar.
    """
    if text.strip():
        fields = text.split()
        new_value = fields[0]
        new_units = "".join(fields[1:])

        if new_units.strip() == "":
            # FIXME: How do we detect a user asking for a dimensionless
            # value vs a user forgetting to specify the unit?
            logger.info("No unit specified. Assuming that it is "
                        "dimensionless")
            new_units = dimensionless

        return UnitScalar(float(new_value), units=new_units)
    else:
        return UnitScalar(0, units=dimensionless)


def unit_scalar_to_str(value, n_digits=6):
    """ Convert a UnitScalar to a string representation to display in text box.
    """
    dimless_labels = [None, 'dimensionless', '1']
    if value is None:
        return ""
    elif isinstance(value, UnitScalar):
        number = value.tolist()
        if isinstance(number, float):
            formatting_str = "{" + "0:.{}g".format(n_digits) + "}"
        elif isinstance(number, int):
            formatting_str = "{0}"
        else:
            msg = "Don't know how to handle UnitScalar with {} as values."
            msg = msg.format(type(number))
            raise NotImplementedError(msg)

        value_repr = formatting_str.format(number)
        if value.units == dimensionless and value.units.label in dimless_labels:  # noqa
            return value_repr
        else:
            return value_repr + " " + str(value.units.label)
    else:
        t = type(value)
        raise ValueError("Got an unexpected value of type {}".format(t))


def UnitScalarEditor():
    """ Edit a UnitScalar value using a TextEditor.

    Note: Returning a TextEditor instead of subclassing it because traitsui
    searches for a very specific pattern when looking for an editor class
    (qt4/foo.py:SimpleEditor, ...).
    """
    return TextEditor(evaluate=str_to_unit_scalar,
                      format_func=unit_scalar_to_str,
                      auto_set=False, enter_set=True)


if __name__ == "__main__":
    from traits.api import HasTraits, Instance
    from traitsui.api import Item, View

    class SampleModel(HasTraits):
        x = Instance(UnitScalar)
        view = View(
            Item("x", editor=UnitScalarEditor())
        )

    model = SampleModel()
    model.configure_traits()
    if model.x is None:
        print("x set to None")
    else:
        print(model.x, model.x.units)

    model = SampleModel()
    model.x = UnitScalar(1, units='1')
    # No units should be seen with this model's view
    model.configure_traits()
