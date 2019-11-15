from unittest import TestCase
from os.path import dirname, isdir, isfile, join
import os
from shutil import rmtree
from contextlib import contextmanager

from app_common.std_lib.filesystem import get_dir_file_count, get_dir_size, \
    get_dir_sizes_cached
from app_common.apptools.cache.txt_file_cache import SingleTxtFileDataCache

HERE = dirname(__file__)


class BaseDirSizeTools(object):
    def setUp(self):
        self.new_folder_name = ".TEST_FOLDER"

    @contextmanager
    def create_temp_folder(self, with_file=False, size=1):
        os.makedirs(self.new_folder_name)
        if with_file:
            # Make a file with 'size' unicode characters in it
            with open(join(self.new_folder_name, "temp.temp"), "w") as f:
                f.write("1" * size)
        try:
            yield
        finally:
            if isdir(self.new_folder_name):
                rmtree(self.new_folder_name)


class TestGetDirFileCount(BaseDirSizeTools, TestCase):

    def test_raise_if_non_existent(self):
        with self.assertRaises(ValueError):
            get_dir_file_count("DOESN'T EXIST")

    def test_empty_folder(self):
        with self.create_temp_folder():
            count = get_dir_file_count(self.new_folder_name)
            self.assertEqual(count, 0)

    def test_non_empty_folder(self):
        count = get_dir_file_count(HERE)
        self.assertGreater(count, 0)

    def test_folder_with_known_content(self):
        with self.create_temp_folder(with_file=True):
            count = get_dir_file_count(self.new_folder_name)
            self.assertEqual(count, 1)

    def test_folder_with_details(self):
        with self.create_temp_folder(with_file=True, size=3):
            count, details = get_dir_file_count(HERE, details=True)
            self.assertIsInstance(count, int)
            self.assertGreater(count, 1)
            self.assertIsInstance(details, dict)
            self.assertIn("", details)

    def test_exclude_no_file(self):
        with self.create_temp_folder(with_file=True, size=3):
            size = get_dir_file_count(self.new_folder_name, exclude="BLAH")
            self.assertEqual(size, 1)

    def test_exclude_all_file(self):
        with self.create_temp_folder(with_file=True, size=3):
            count = get_dir_file_count(self.new_folder_name, exclude=".")
            self.assertAlmostEqual(count, 0.)

    def test_exclude_the_file(self):
        with self.create_temp_folder(with_file=True, size=3):
            count = get_dir_file_count(self.new_folder_name, exclude="temp.+")
            self.assertEqual(count, 0)


class TestGetDirSize(BaseDirSizeTools, TestCase):

    def test_raise_if_non_existent(self):
        with self.assertRaises(ValueError):
            get_dir_size("DOESN'T EXIST")

    def test_empty_folder(self):
        with self.create_temp_folder():
            size = get_dir_size(self.new_folder_name)
            self.assertEqual(size, 0)

    def test_non_empty_folder(self):
        size = get_dir_size(HERE)
        self.assertGreater(size, 0)

    def test_folder_with_known_content(self):
        new_folder_name = self.new_folder_name
        num_character = 3
        with self.create_temp_folder(with_file=True, size=num_character):
            size = get_dir_size(new_folder_name, unit="B")
            self.assertAlmostEqual(size, num_character)
            size = get_dir_size(new_folder_name, unit="KB")
            self.assertAlmostEqual(size, num_character * 1.e-3)
            size = get_dir_size(new_folder_name, unit="MB")
            self.assertAlmostEqual(size, num_character * 1.e-6)
            size = get_dir_size(new_folder_name, unit="GB")
            self.assertAlmostEqual(size, num_character * 1.e-9)

        num_character = 5
        with self.create_temp_folder(with_file=True, size=num_character):
            size = get_dir_size(new_folder_name, unit="B")
            self.assertAlmostEqual(size, num_character)

    def test_folder_with_details(self):
        with self.create_temp_folder(with_file=True, size=3):
            size, details = get_dir_size(HERE, unit="B", details=True)
            self.assertIsInstance(size, float)
            self.assertGreater(size, 0.)
            self.assertIsInstance(details, dict)
            self.assertIn("", details)

    def test_exclude_no_file(self):
        with self.create_temp_folder(with_file=True, size=3):
            size = get_dir_size(self.new_folder_name, unit="B", exclude="BLAH")
            self.assertAlmostEqual(size, 3.)

    def test_exclude_all_file(self):
        with self.create_temp_folder(with_file=True, size=3):
            size = get_dir_size(self.new_folder_name, unit="B", exclude=".")
            self.assertAlmostEqual(size, 0.)

    def test_exclude_the_file(self):
        with self.create_temp_folder(with_file=True, size=3):
            size = get_dir_size(self.new_folder_name, unit="B",
                                exclude="temp.+")
            self.assertAlmostEqual(size, 0.)


class TestCachedGetDirSizes(BaseDirSizeTools, TestCase):
    def setUp(self):
        super(TestCachedGetDirSizes, self).setUp()
        self.cache_path = ".sample_cache.json"
        open(self.cache_path, "w").write("{}")

    def tearDown(self):
        if isfile(self.cache_path):
            os.remove(self.cache_path)

    def test_cache_new_file(self):
        new_file = "new_file.json"
        if isfile(new_file):
            os.remove(new_file)

        try:
            sizes = get_dir_sizes_cached([HERE], cache_filepath=new_file)
            self.assertEqual(len(sizes), 1)
            self.assertIsInstance(sizes[0], float)
        finally:
            if isfile(new_file):
                os.remove(new_file)

    def test_get_sizes_no_cache(self):
        sizes = get_dir_sizes_cached([HERE], cache_filepath="")
        self.assertEqual(len(sizes), 1)
        self.assertIsInstance(sizes[0], float)

    def test_raise_folder_non_existent(self):
        with self.assertRaises(ValueError):
            get_dir_sizes_cached(["DOESN'T EXIST"],
                                 cache_filepath=self.cache_path)

    def test_empty_folder(self):
        with self.create_temp_folder():
            sizes = get_dir_sizes_cached([self.new_folder_name],
                                         self.cache_path)
            self.assertEqual(len(sizes), 1)
            self.assertEqual(sizes, [0])
            # Check that one can pass a name alone:
            sizes = get_dir_sizes_cached(self.new_folder_name, self.cache_path)
            self.assertEqual(sizes, [0])

    def test_non_empty_folder(self):
        sizes = get_dir_sizes_cached([HERE], self.cache_path)
        self.assertGreater(sizes[0], 0)
        sizes2 = get_dir_sizes_cached([HERE], self.cache_path)
        self.assertEqual(sizes, sizes2)
        cache_content = open(self.cache_path, "r").read()

        # Check the content of the file, which stored in bytes:
        sizes = get_dir_sizes_cached([HERE], self.cache_path, unit="B")
        # null for the fact that there is no metadata stored:
        expected = '{"%s": [%s, null]}' % (HERE, sizes[0])
        # On windows, the path separators get doubled because escaped:
        self.assertEqual(expected, cache_content.replace("\\\\", "\\"))

    def test_read_from_cache(self):
        made_up_size = 123
        sizes = get_dir_sizes_cached([HERE], self.cache_path)
        # Make sure that the size is wrong, to make sure get_dir_sizes_cached
        # doesn't recompute if the file exists:
        self.assertNotAlmostEqual(sizes[0], made_up_size)

        # Write the cache file:
        cache = SingleTxtFileDataCache(url=self.cache_path)
        cache.set_value(HERE, made_up_size)
        cache.close()

        sizes = get_dir_sizes_cached(HERE, self.cache_path, unit="B")
        self.assertAlmostEqual(sizes[0], made_up_size)

    def test_folder_with_known_content(self):
        new_folder_name = self.new_folder_name
        num_character = 3
        with self.create_temp_folder(with_file=True, size=num_character):
            sizes = get_dir_sizes_cached(new_folder_name, self.cache_path,
                                         unit="B")
            self.assertAlmostEqual(sizes[0], num_character)
            sizes = get_dir_sizes_cached(new_folder_name, self.cache_path,
                                         unit="KB")
            self.assertAlmostEqual(sizes[0], num_character * 1.e-3)
            sizes = get_dir_sizes_cached(new_folder_name, self.cache_path,
                                         unit="MB")
            self.assertAlmostEqual(sizes[0], num_character * 1.e-6)
            sizes = get_dir_sizes_cached(new_folder_name, self.cache_path,
                                         unit="GB")
            self.assertAlmostEqual(sizes[0], num_character * 1.e-9)
