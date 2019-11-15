from unittest import TestCase, skipIf
from os.path import abspath, dirname, expanduser
import os

from app_common.pyface.ui.extra_file_dialogs import FileDialogWithMemory

HERE = abspath(dirname(__file__))


skip = (os.environ.get("ETS_TOOLKIT", "qt4") == "null")


@skipIf(skip, "No UI backend to paint UIs into.")
class TestFileDialogWithMemory(TestCase):
    def setUp(self):
        self.homepath = expanduser('~')

    def tearDown(self):
        # Reset
        FileDialogWithMemory.last_directory = ""

    def test_initial_value_default_dir(self):
        fd = FileDialogWithMemory()
        self.assertEqual(fd.default_directory, self.homepath)

    def test_loaded_from_new_location(self):
        # This reproduces what close does
        FileDialogWithMemory.last_directory = HERE

        fd = FileDialogWithMemory()
        self.assertEqual(fd.default_directory, HERE)

    def test_reset_last_directory(self):
        # This reproduces what close does
        FileDialogWithMemory.last_directory = HERE
        fd = FileDialogWithMemory()
        self.assertNotEqual(fd.default_directory, self.homepath)
        FileDialogWithMemory.last_directory = ""
        fd = FileDialogWithMemory()
        self.assertEqual(fd.default_directory, self.homepath)
