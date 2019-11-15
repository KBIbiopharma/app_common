from unittest import TestCase, skipIf
import os
from traits.api import HasTraits, Instance
from traitsui.api import Item, View
try:
    from scimath.units.api import UnitScalar
    from scimath.units.dimensionless import dimensionless
    from app_common.traitsui.unit_scalar_editor import \
        UnitScalarEditor, str_to_unit_scalar, unit_scalar_to_str

    scimath_available = True
except ImportError:
    scimath_available = False

if scimath_available:
    class SampleModel(HasTraits):
        x = Instance(UnitScalar)
        view = View(
            Item("x", editor=UnitScalarEditor())
        )

skip = (os.environ.get("ETS_TOOLKIT", "qt4") == "null" or
        scimath_available is False)
if not skip:
    from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant

    @skipIf(skip, "No scimath available or no UI backend to paint UIs into.")
    class TestUniScalarEditor(TestCase, GuiTestAssistant):
        def setUp(self):
            GuiTestAssistant.setUp(self)
            self.model = SampleModel()
            self.ui = None

        def tearDown(self):
            GuiTestAssistant.tearDown(self)
            if self.ui is not None:
                self.ui.dispose()

        def test_editor_with_value(self):
            val = UnitScalar(2, units="cm")
            self.model.x = val
            self.ui = self.model.edit_traits()
            self.assertEqual(self.model.x, val)

        def test_editor_without_value(self):
            self.ui = self.model.edit_traits()
            self.assertIsNone(self.model.x)

        def test_editor_with_complex_unit(self):
            val = UnitScalar(2, units="cm / s")
            self.model.x = val
            self.ui = self.model.edit_traits()
            self.assertEqual(self.model.x, val)

        def test_displayed_text(self):
            self.model.x = UnitScalar(2, units=dimensionless)
            with self.event_loop():
                self.ui = self.model.edit_traits()
                text = get_text_editor_for_attr(self.ui, "x")

            self.assertEqual(text, '2')

        def test_change_text(self):
            # The event loop is needed for the change in the UI editor to
            # modify the model.
            with self.event_loop():
                self.ui = self.model.edit_traits()
                set_text_editor_for_attr(self.ui, "x", "2 km")

            self.assertEqual(self.model.x, UnitScalar(2, units="km"))

        def test_units_label_with_int(self):
            self.model.x = UnitScalar(2, units="g")
            with self.event_loop():
                self.ui = self.model.edit_traits()
                text = get_text_editor_for_attr(self.ui, "x")

            self.assertEqual(text, '2 g')

        def test_units_label_with_float(self):
            self.model.x = UnitScalar(2.1, units="g")
            with self.event_loop():
                self.ui = self.model.edit_traits()
                text = get_text_editor_for_attr(self.ui, "x")

            self.assertEqual(text, '2.1 g')


@skipIf(skip, "No scimath available or no UI backend to paint UIs into.")
class TestConversionFunctions(TestCase):
    def test_str2val_with_int(self):
        text = "2 cm"
        self.assertEqual(str_to_unit_scalar(text), UnitScalar(2, units="cm"))

    def test_str2val_with_float_period(self):
        text = "2. cm"
        self.assertEqual(str_to_unit_scalar(text), UnitScalar(2., units="cm"))

    def test_str2val_with_float(self):
        text = "2.0 cm"
        self.assertEqual(str_to_unit_scalar(text), UnitScalar(2.0, units="cm"))

    def test_str2val_with_float_high_precision(self):
        text = "2.012345678901 cm"
        self.assertAlmostEqual(str_to_unit_scalar(text),
                               UnitScalar(2.012345678901, units="cm"))

    def test_basic_val2str(self):
        val = UnitScalar(2, units="cm")
        self.assertEqual(unit_scalar_to_str(val), "2 cm")

    def test_cplx_str2val(self):
        text = "2.1 cm /   s"
        self.assertEqual(str_to_unit_scalar(text),
                         UnitScalar(2.1, units="cm/s"))

    def test_cplx_val2str(self):
        val = UnitScalar(2.1, units="cm/s")
        self.assertEqual(unit_scalar_to_str(val), "2.1 cm/s")

    def test_empty_str2val(self):
        text = "  "
        self.assertEqual(str_to_unit_scalar(text), UnitScalar(0, units='1'))

    def test_empty_val2str(self):
        self.assertEqual(unit_scalar_to_str(None), "")

    def test_dimless_val2str(self):
        ph_val = UnitScalar(3, units="1")
        self.assertEqual(unit_scalar_to_str(ph_val), "3")

        ph_val2 = UnitScalar(3, units=dimensionless)
        self.assertEqual(unit_scalar_to_str(ph_val2), "3")


def get_text_editor_for_attr(traits_ui, attr):
    """ Grab the Qt QLineEdit for attr off the UI and return its text.
    """
    widget = get_widget_for_attr(traits_ui, attr)
    return widget.text()


def set_text_editor_for_attr(traits_ui, attr, val):
    """ Grab the Qt QLineEdit for attr off the UI and set its text to val.

    This needs to trigger the right event (Qt signal) so that TraitsUI gets
    notified.
    """
    widget = get_widget_for_attr(traits_ui, attr)
    widget.setText(val)
    # Emit the signal that TraitsUI is listening to:
    widget.editingFinished.emit()


def get_widget_for_attr(traits_ui, attr_name):
    """ Return the Qt widget in the UI which displays the attribute specified.
    """
    x_editor = traits_ui.get_editors(attr_name)[0]
    qt_widget = x_editor.control
    return qt_widget
