from unittest import TestCase, skipIf
import os

from app_common.traitsui.common_modal_dialogs import request_string, \
    request_string_selection, StrRequesterDlg, GuiStringSelector
from app_common.apptools.testing_utils import assert_obj_gui_works
from traits.etsconfig.api import ETSConfig  # noqa

toolkit = ETSConfig.toolkit

if toolkit == 'qt4':
    api = os.environ.get("QT_API", "")
    if api == "pyside":
        from PySide.QtGui import QLineEdit, QComboBox
    elif api in ["pyqt", ""]:
        from PyQt4.QtGui import QLineEdit, QComboBox
    else:
        raise ImportError("QT_API={} not supported!".format(api))

NO_UI_BACKEND = toolkit == "null"


@skipIf(NO_UI_BACKEND, "No UI backend to paint into.")
class TestRequestString(TestCase):
    def test_bring_up_default(self):
        ui = request_string(dlg_kind=None)
        try:
            self.assertIsInstance(ui.info.object, StrRequesterDlg)
            self.assertIsInstance(ui._editors[2].control, QLineEdit)
        finally:
            ui.dispose()

    def test_bring_up_with_forbidden_values(self):
        ui = request_string(dlg_kind=None, forbidden_values={"blah"})
        try:
            self.assertIsInstance(ui.info.object, StrRequesterDlg)
            self.assertIsInstance(ui._editors[2].control, QLineEdit)
        finally:
            ui.dispose()

        ui = request_string(dlg_kind=None, forbidden_values=["blah"])
        try:
            self.assertIsInstance(ui.info.object, StrRequesterDlg)
            self.assertIsInstance(ui._editors[2].control, QLineEdit)
        finally:
            ui.dispose()

    def test_control_view(self):
        ui = request_string(dlg_kind=None, view_width=200, title="BLAH")
        try:
            self.assertIsInstance(ui.info.object, StrRequesterDlg)
        finally:
            ui.dispose()


@skipIf(NO_UI_BACKEND, "No UI backend to paint into.")
class TestRequestSelectingString(TestCase):

    def test_selected_string_initial_selection(self):
        selector = GuiStringSelector(string_options=list("abcd"))
        self.assertEqual(selector.selected_string, "")

    def test_bringup_gui_string_selector(self):
        selector = GuiStringSelector(string_options=list("abcd"))
        assert_obj_gui_works(selector)

    def test_bring_up_default_via_function(self):
        ui = request_string_selection(list("abcd"), dlg_kind=None)
        try:
            self.assertIsInstance(ui.info.object, GuiStringSelector)
            self.assertIsInstance(ui._editors[2].control, QComboBox)
        finally:
            ui.dispose()

    def test_control_view_via_function(self):
        ui = request_string_selection(list("abcd"), dlg_kind=None,
                                      view_width=200, title="BLAH")
        try:
            self.assertIsInstance(ui.info.object, GuiStringSelector)
            self.assertIsInstance(ui._editors[2].control, QComboBox)
        finally:
            ui.dispose()
