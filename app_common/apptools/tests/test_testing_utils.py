from unittest import TestCase
from os.path import isdir, isfile, join

from app_common.apptools.testing_utils import temp_folder


class TestTempFolder(TestCase):
    def test_temp_empty_folder(self):
        with temp_folder() as path:
            self.assertIsInstance(path, str)
            self.assertTrue(isdir(path))

        self.assertFalse(isdir(path))

    def test_temp_non_empty_folder(self):
        with temp_folder() as path:
            self.assertIsInstance(path, str)
            self.assertTrue(isdir(path))
            with open(join(path, "temp.txt"), "w") as f:
                f.write("BLAH")
            self.assertTrue(isfile(join(path, "temp.txt")))

        self.assertFalse(isdir(path))
