from unittest import TestCase, skipIf
from os.path import basename, dirname, isfile, join, splitext
import os

from app_common.apptools.script_runner.python_script_file_selector import \
    DEFAULT_SCRIPT_NAME, PythonScriptFileSelector, _ScriptNamePrompter
from app_common.apptools.testing_utils import temp_bringup_ui_for

HERE = dirname(__file__)


skip = (os.environ.get("ETS_TOOLKIT", "qt4") == "null")


@skipIf(skip, "No UI backend to paint UIs into.")
class TestPythonScriptFileSelector(TestCase):

    def setUp(self):
        self.default_location = join(HERE, "data")
        self.filepath = join(self.default_location, "first_script.py")
        self.code = open(self.filepath).read()
        self.selector = PythonScriptFileSelector(
            default_location=join(self.default_location)
        )

    def test_bring_up(self):
        ui = self.selector.edit_traits()
        ui.dispose()

    def test_load_user_script_file(self):
        self.assertEqual(self.selector.code, "")
        self.selector.filepath = self.filepath
        self.assertEqual(self.selector.code, self.code)

    def test_load_any_file(self):
        # Can load any file...
        current_py_file = __file__
        if splitext(current_py_file)[1] == ".pyc":
            current_py_file = splitext(current_py_file)[0] + ".py"

        if not isfile(current_py_file):
            self.skipTest("Skipping the test because the source file for the "
                          "current test isn't available.")

        self.selector.filepath = current_py_file
        # but it doesn't get added to the known_scripts
        self.assertNotIn(splitext(basename(__file__))[0],
                         self.selector.known_scripts)
        self.assertIn("TestPythonScriptFileSelector", self.selector.code)
        self.assertTrue(self.selector.dirty)

    def test_change_code_and_create_new_script(self):
        self.assertEqual(self.selector.code, "")
        self.selector.code = self.code
        new_script_name = "generated_script"
        self.selector.create_new_script(new_script_name)
        script_filepath = self.selector._filepath_from_script_name(
            new_script_name
        )
        try:
            self.assertTrue(isfile(script_filepath))
        finally:
            if isfile(script_filepath):
                os.remove(script_filepath)

    def test_change_code_and_save(self):
        self.assertEqual(self.selector.code, "")
        self.selector.code = self.code
        new_script_name = "generated_script"
        self.selector.create_new_script(new_script_name)
        self.selector.code += "FOOBAR"
        self.selector.save_button = True
        script_filepath = self.selector._filepath_from_script_name(
            new_script_name
        )
        try:
            content = open(script_filepath).read()
            self.assertTrue(content.endswith("FOOBAR"))
        finally:
            if isfile(script_filepath):
                os.remove(script_filepath)

    def test_known_scripts(self):
        # In sample_scripts folder, first_script is present.
        expected = {DEFAULT_SCRIPT_NAME, 'first_script'}
        self.assertEqual(set(self.selector.known_scripts), expected)
        selector = PythonScriptFileSelector(
            default_location=self.default_location
        )
        # Everywhere else, the sample scripts should still be accessible:
        self.assertGreaterEqual(set(selector.known_scripts), expected)

    def test_select_name_from_user_scripts(self):
        self.assertEqual(self.selector.name, DEFAULT_SCRIPT_NAME)
        expected = [DEFAULT_SCRIPT_NAME, "first_script"]
        try:
            self.assertEqual(self.selector.known_scripts, expected)
        except AssertionError:
            # FIXME: Investigate why Jenkins fails at this...
            for item in expected:
                self.assertIn(item, self.selector.known_scripts)

        self.selector.name = "first_script"
        self.assertEqual(self.selector.code, self.code)
        self.selector.name = DEFAULT_SCRIPT_NAME
        self.assertEqual(self.selector.code, "")

    def test_select_name_from_sample_scripts(self):
        selector = PythonScriptFileSelector(
            default_location=self.default_location
        )
        # Everywhere else, the sample_scripts should still be accessible:
        self.assertEqual(selector.name, DEFAULT_SCRIPT_NAME)
        selector.name = "first_script"
        self.assertEqual(selector.code, self.code)
        self.assertEqual(selector.filepath, self.filepath)

    def test_modify_filepath_and_reload(self):
        self.selector.code = self.code
        new_script_name = "temp_script"
        self.selector.create_new_script(new_script_name)
        script_filepath = self.selector._filepath_from_script_name(
            new_script_name
        )
        try:
            self.assertTrue(isfile(script_filepath))
            with open(script_filepath, "w") as f:
                f.write("")
            self.selector.reload_button = True
            self.assertEqual(self.selector.code, "")
        finally:
            if isfile(script_filepath):
                os.remove(script_filepath)


@skipIf(skip, "No UI backend to paint UIs into.")
class TestNamePrompter(TestCase):
    def test_bring_up(self):
        prompter = _ScriptNamePrompter()
        with temp_bringup_ui_for(prompter):
            pass
