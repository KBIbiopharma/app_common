from unittest import skipIf, TestCase
import os
from traits.testing.unittest_tools import UnittestTools

from app_common.model_tools.data_editor import DataElement, \
    DataElementEditor

no_toolkit = os.environ["ETS_TOOLKIT"] == "null"


@skipIf(no_toolkit, "No toolkit to paint the editors")
class TestDataElementEditor(TestCase, UnittestTools):

    def test_long_name_handling(self):
        obj = DataElement(name="ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRS")
        editor = DataElementEditor(obj=obj)
        # Long names are truncated at 25:
        self.assertEqual(editor.name, "ABCDEFGHIJKLMNOPQRSTUVWXY")
        self.assertEqual(editor.tooltip, obj.name)

    def test_short_name_handling(self):
        obj = DataElement(name="FOO")
        editor = DataElementEditor(obj=obj)
        self.assertEqual(editor.name, obj.name)
        self.assertEqual(editor.tooltip, obj.name)

    def test_name_updates(self):
        obj = DataElement(name="FOOBAR")
        editor = DataElementEditor(obj=obj)
        with self.assertTraitChanges(editor, "name", 1):
            obj.name = "FOOBAR2"

        self.assertEqual(editor.name, obj.name)
