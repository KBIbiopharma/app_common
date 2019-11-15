from unittest import TestCase

from app_common.std_lib.file_ext import is_csv_file, is_excel_file, \
    is_hdf_file, is_py_file, generate_is_ext_file


class TestFileExt(TestCase):
    def test_is_py_file(self):
        self.assertTrue(is_py_file("blah.py"))
        self.assertTrue(is_py_file("foo.py"))

    def test_not_is_py_file(self):
        self.assertFalse(is_py_file("blah.pyc"))
        self.assertFalse(is_py_file("blah.foo"))

    def test_is_csv_file(self):
        self.assertTrue(is_csv_file("blah.csv"))
        self.assertTrue(is_csv_file("foo.csv"))

    def test_not_is_csv_file(self):
        self.assertFalse(is_csv_file("blah.pyc"))
        self.assertFalse(is_csv_file("blah.foo"))

    def test_is_excel_file(self):
        self.assertTrue(is_excel_file("blah.xls"))
        self.assertTrue(is_excel_file("foo.xlsx"))

    def test_not_is_excel_file(self):
        self.assertFalse(is_excel_file("blah.xlsc"))
        self.assertFalse(is_excel_file("blah.foo"))

    def test_is_hdf_file(self):
        self.assertTrue(is_hdf_file("blah.h5"))
        self.assertTrue(is_hdf_file("foo.hdf5"))

    def test_not_is_hdf_file(self):
        self.assertFalse(is_hdf_file("blah.h5c"))
        self.assertFalse(is_hdf_file("blah.foo"))


class TestGenerateIsExtFile(TestCase):

    def test_generate_is_ext_file_1_ext(self):
        test_func1 = generate_is_ext_file({".pyc"})
        self.assertTrue(test_func1("foo.pyc"))

    def test_generate_is_ext_file_2_exts(self):
        test_func1 = generate_is_ext_file({".py", ".pyc"})
        self.assertTrue(test_func1("foo.py"))
        self.assertTrue(test_func1("foo.pyc"))
        self.assertFalse(is_py_file("blah.foo"))

    def test_generate_is_ext_file_2_exts_with_list(self):
        test_func1 = generate_is_ext_file([".py", ".pyc"])
        self.assertTrue(test_func1("foo.py"))
        self.assertTrue(test_func1("foo.pyc"))
        self.assertFalse(is_py_file("blah.foo"))
