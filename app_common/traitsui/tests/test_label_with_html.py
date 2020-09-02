from unittest import TestCase
from traits.api import HasTraits
from traitsui.api import View

from app_common.traitsui.label_with_html import Label
from app_common.apptools.testing_utils import temp_bringup_ui_for


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
        with temp_bringup_ui_for(A()) as ui:
            main_group = ui.view_elements.content["view"].content.content[0]
            item = main_group.content[0]
            self.assertEqual(item.label, '<p style=color:black>blah</p>')

            item = main_group.content[1]
            self.assertEqual(item.label, '<b><p style=color:red>blah</p></b>')

            item = main_group.content[2]
            self.assertEqual(item.label,
                             '<i><b><p style=color:#f133a0>blah</p></b></i>')

            item = main_group.content[3]
            self.assertEqual(item.label,
                             '<p style=color:tomato;font-family:verdana;font-size:48px>blah</p>')  # noqa

            item = main_group.content[4]
            self.assertEqual(item.label,
                             '<p style=color:black;background-color:powderblue>blah</p>')  # noqa
