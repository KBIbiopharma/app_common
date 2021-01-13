from unittest import TestCase
from traits.api import Int, Range, Str, TraitError

from app_common.traitsui.dict_editors import DictValueEditor
from app_common.apptools.testing_utils import assert_obj_gui_works


class TestDictValueEditor(TestCase):

    def test_create_no_dict(self):
        with self.assertRaises(ValueError):
            DictValueEditor()

    def test_create_dict_as_arg(self):
        target = {"a": 1}
        editor = DictValueEditor(target)
        self.assertEqual(editor.target_dict, target)
        self.assertIn("a", editor.traits())

    def test_bring_up_ui(self):
        assert_obj_gui_works(DictValueEditor(target_dict={"a": 1, "b": 2}))

    def test_change_trait_changes_float_dict(self):
        editor = DictValueEditor(target_dict={"a": 1.1, "b": 2.2})
        self.assertIn("a", editor.traits())
        self.assertEqual(editor.a, 1.1)
        self.assertIn("b", editor.traits())
        self.assertEqual(editor.b, 2.2)

        editor.a = 3.3
        self.assertEqual(editor.target_dict["a"], 3.3)
        editor.b = -1.1
        self.assertEqual(editor.target_dict["b"], -1.1)

    def test_change_trait_changes_int_dict(self):
        editor = DictValueEditor(target_dict={"a": 1, "b": 2},
                                 value_to_trait=Int)
        self.assertIn("a", editor.traits())
        self.assertEqual(editor.a, 1)
        self.assertIsInstance(editor.a, int)
        self.assertIn("b", editor.traits())
        self.assertEqual(editor.b, 2)
        self.assertIsInstance(editor.b, int)

        editor.a = 3
        self.assertEqual(editor.target_dict["a"], 3)
        editor.b = -1
        self.assertEqual(editor.target_dict["b"], -1)

    def test_change_trait_changes_str_dict(self):
        editor = DictValueEditor(target_dict={"a": "1", "b": "2"},
                                 value_to_trait=Str)
        self.assertIn("a", editor.traits())
        self.assertEqual(editor.a, "1")
        self.assertIn("b", editor.traits())
        self.assertEqual(editor.b, "2")

        editor.a = "foo"
        self.assertEqual(editor.target_dict["a"], "foo")
        editor.b = "bar"
        self.assertEqual(editor.target_dict["b"], "bar")

    def test_set_values_1_val(self):
        editor = DictValueEditor(target_dict={"a": 1.1, "b": 2.2})
        editor.set_values(**{"a": 3})
        self.assertEqual(editor.target_dict["a"], 3.)
        self.assertEqual(editor.a, 3.)

    def test_transform_keys(self):
        editor = DictValueEditor(target_dict={"a a": 1, "b*c": 2})
        self.assertIn("a_a", editor.traits())
        self.assertEqual(editor.a_a, 1)
        self.assertIn("b_c", editor.traits())
        self.assertEqual(editor.b_c, 2)

        editor.b_c = 3
        self.assertEqual(editor.target_dict["b*c"], 3)

    def test_value_to_trait_func(self):
        value_to_trait = lambda value: Range(low=0, high=10, value=value)
        editor = DictValueEditor(target_dict={"a": 1, "b": 2},
                                 value_to_trait=value_to_trait)
        self.assertIn("a", editor.traits())
        self.assertEqual(editor.a, 1)
        self.assertIsInstance(editor.a, int)
        self.assertIn("b", editor.traits())
        self.assertEqual(editor.b, 2)
        self.assertIsInstance(editor.b, int)

        editor.a = 3
        self.assertEqual(editor.target_dict["a"], 3)
        # Impossible because of the Range:
        with self.assertRaises(TraitError):
            editor.b = -1
        self.assertEqual(editor.target_dict["b"], 2)

    def test_set_values_2_vals(self):
        editor = DictValueEditor(target_dict={"a": 1.1, "b": 2.2, "c": 3.2})
        editor.set_values(**{"a": 3, "c": 3.3})
        self.assertEqual(editor.target_dict["a"], 3.)
        self.assertEqual(editor.a, 3.)

        self.assertEqual(editor.target_dict["c"], 3.3)
        self.assertEqual(editor.c, 3.3)
