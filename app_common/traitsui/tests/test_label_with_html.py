from unittest import TestCase
from traits.api import HasTraits
from traitsui.api import View

from app_common.traitsui.label_with_html import Label
from app_common.apptools.testing_utils import assert_obj_gui_works


class A(HasTraits):
    view = View(
        Label("blah"),
        Label("blah", color="red", bold=True),
        Label("blah", color="#f133a0", bold=True, italic=True),
        Label("blah", color="tomato", font_family="verdana",
              font_size=48),
        Label("blah", bg_color="powderblue"),
    )


class TestLabel(TestCase):
    def test_ui(self):
        assert_obj_gui_works(A())
