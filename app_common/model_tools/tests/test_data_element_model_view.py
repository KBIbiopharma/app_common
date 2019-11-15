import os
from unittest import TestCase, skipIf
from traitsui.api import ModelView
from traits.api import adapt, AdaptationError, Float, register_factory
from traits.adaptation.adaptation_manager import get_global_adaptation_manager

try:
    from app_common.model_tools.data_element import DataElement
    from app_common.model_tools.data_element_model_view import \
        DataElementModelView
    from app_common.model_tools.data_editor import DataElementEditor
    from app_common.apptools.testing_utils import temp_bringup_ui_for

    no_scimath = False
except ImportError:
    no_scimath = True


skip = (os.environ.get("ETS_TOOLKIT", "qt4") == "null" or no_scimath)


class BaseDataElementModelView(object):
    def tearDown(self):
        # Clear up the adaptation manager to avoid leakages between tests:
        # FIXME: undocument way to do this! There should be an official way.
        manager = get_global_adaptation_manager()
        manager._adaptation_offers.clear()

    def test_bring_up(self):
        view = DataElementModelView(model=self.model)
        with temp_bringup_ui_for(view):
            pass

    def test_adapt_to_model_view(self):
        with self.assertRaises(AdaptationError):
            adapt(self.model, ModelView)

        register_factory(DataElementModelView, DataElement, ModelView)
        result = adapt(self.model, ModelView)
        self.assertIsInstance(result, DataElementModelView)

    def test_adapt_into_split_area_editor_pane(self):
        register_factory(DataElementModelView, DataElement, ModelView)

        editor = DataElementEditor(obj=self.model)
        editor._create_control(None)
        try:
            self.assertIsInstance(editor.obj_view, DataElementModelView)
        finally:
            editor.traits_ui.dispose()


@skipIf(skip, "No UI backend to paint UIs into or missing scimath.")
class TestDataElementModelView(BaseDataElementModelView, TestCase):
    def setUp(self):
        self.model = DataElement(name="Blah")


@skipIf(skip, "No UI backend to paint UIs into or missing scimath.")
class TestDataElementModelViewSubclass(BaseDataElementModelView, TestCase):
    def setUp(self):

        class A(DataElement):
            data = Float

        self.model = A(name="blah", data=2.)
