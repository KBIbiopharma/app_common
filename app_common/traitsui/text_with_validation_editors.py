from __future__ import print_function

import logging
from warnings import warn

from traits.api import Bool, Callable, Either, List, Set, Str
from traitsui.api import TextEditor

logger = logging.getLogger(__name__)


class TextWithExcludedValuesEditor(TextEditor):
    """ Edit a string, invalidating if in provided forbidden set of values.
    """
    enter_set = Bool(True)

    auto_set = Bool(True)

    forbidden_values = Either(Set, List)

    evaluate = Callable

    def __init__(self, *args, **traits):
        super(TextWithExcludedValuesEditor, self).__init__(*args, **traits)
        if not isinstance(self.forbidden_values, set):
            msg = "For best performance, TextWithExcludedValuesEditor's " \
                  "forbidden_values can be provided as a set instead of a {}."
            msg = msg.format(type(self.forbidden_values))
            warn(msg)

    def _evaluate_default(self):
        def evaluate(input):
            if input in self.forbidden_values:
                return None

            return input
        return evaluate


if __name__ == "__main__":
    from traits.api import HasTraits
    from traitsui.api import Item, View

    class SampleModel(HasTraits):
        x = Str()
        view = View(
            Item("x",
                 editor=TextWithExcludedValuesEditor(forbidden_values=["a"]))
        )

    model = SampleModel()
    model.configure_traits()
    if model.x is None:
        print("x set to None")
    else:
        print(model.x)
