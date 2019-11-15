from unittest import TestCase, skipIf
import os
from traits.api import HasTraits, Int
from traitsui.api import Item, Group, View

from app_common.apptools.testing_utils import temp_bringup_ui_for
from app_common.traitsui.common_traitsui_groups import \
    make_window_title_group

NO_UI_BACKEND = os.environ.get("ETS_TOOLKIT", "qt4") == "null"


class A(HasTraits):
    a = Int


@skipIf(NO_UI_BACKEND, "No UI backend")
class TestMakeUITitle(TestCase):
    def test_make_title(self):
        title = "BLAH BLAH"
        group = make_window_title_group(title)
        self.assertIsInstance(group, Group)

    def test_make_title_control_size(self):
        title = "BLAH BLAH"
        group = make_window_title_group(title, title_size=3)
        self.assertIsInstance(group, Group)

    def test_make_title_control_blanks(self):
        title = "BLAH BLAH"
        group = make_window_title_group(title, title_size=3,
                                        include_blank_spaces=False)
        self.assertIsInstance(group, Group)

    def test_make_title_control_alignment(self):
        title = "BLAH BLAH"
        group = make_window_title_group(title, title_size=3, align="right",
                                        include_blank_spaces=False)
        self.assertIsInstance(group, Group)

    def test_make_title_group(self):
        title = "BLAH BLAH"
        view = View(
            make_window_title_group(title),
            Item("a")
        )
        self.assert_bring_up_for_view(view)

    def test_make_title_group_with_alignment(self):
        title = "BLAH BLAH"
        view = View(
            make_window_title_group(title, align="left"),
            Item("a")
        )
        self.assert_bring_up_for_view(view)

    def test_make_title_group_without_padding(self):
        title = "BLAH BLAH"
        view = View(
            make_window_title_group(title, include_blank_spaces=False),
            Item("a")
        )
        self.assert_bring_up_for_view(view)

    # Helper ------------------------------------------------------------------

    def assert_bring_up_for_view(self, view):
        model = A()
        model.view = view
        with temp_bringup_ui_for(model):
            pass
