from unittest import skipIf, TestCase
from os.path import dirname, isdir, isfile, join
import os
import datetime as dt
from os.path import expanduser
from shutil import rmtree
from contextlib import contextmanager

from app_common.std_lib.filepath_utils import attempt_empty_folder, \
    open_file, rotate_filename, string2filename, sync_folders

NO_GUI = os.environ.get("ETS_TOOLKIT", "qt4") == "null"

HERE = dirname(__file__)


class TestStringToFilename(TestCase):
    def test_just_letters(self):
        string = "abcde"
        result = string2filename(string)
        self.assertEqual(result, string)

    def test_letter_and_number(self):
        string = "abcde12345"
        result = string2filename(string)
        self.assertEqual(result, string)

    def test_letter_number_and_underscores(self):
        string = "abcde_12345_fghi"
        result = string2filename(string)
        self.assertEqual(result, string)

    def test_remove_trailing_underscores(self):
        string = "abcde_"
        result = string2filename(string)
        self.assertEqual(result, "abcde")

    def test_remove_bad_characters(self):
        string = "a/b:c-d=e+z(f)g[h]i{j}k"
        result = string2filename(string)
        self.assertEqual(result, "a_b_c_d_e_z_f_g_h_i_j_k")

    def test_remove_multiple_underscores(self):
        string = "a__b"
        result = string2filename(string)
        self.assertEqual(result, "a_b")

    def test_remove_multiple_underscores_generated(self):
        string = "a-/b"
        result = string2filename(string)
        self.assertEqual(result, "a_b")


class TestRotateFilename(TestCase):
    def setUp(self):
        self.test_dir = join(HERE, "temp")
        if isdir(self.test_dir):
            rmtree(self.test_dir)

        os.makedirs(self.test_dir)

    def tearDown(self):
        if isdir(self.test_dir):
            rmtree(self.test_dir)

    def test_rotate_filename_no_collision(self):
        fname = join(self.test_dir, "test.py")
        rotated_name = rotate_filename(fname)
        self.assertEqual(fname, rotated_name)

    def test_rotate_filename_1_collision(self):
        fname = join(self.test_dir, "test.py")
        self.create_files(fname)
        rotated_name = rotate_filename(fname)
        expected = join(self.test_dir, "test_v2.py")
        self.assertEqual(rotated_name, expected)

    def test_rotate_filename_n_collision(self):
        n = 10
        fname = join(self.test_dir, "test.py")
        self.create_files(fname)
        for i in range(2, n):
            other_fname = join(self.test_dir, "test_v{}.py".format(i))
            self.create_files(other_fname)

        rotated_name = rotate_filename(fname)
        expected = join(self.test_dir, "test_v{}.py".format(n))
        self.assertEqual(rotated_name, expected)

    # Helper methods ----------------------------------------------------------

    def create_files(self, fname):
        with open(fname, "w") as f:
            f.write(" ")


class TestEmptyFolder(TestCase):

    def test_empty_folder_non_existent(self):
        # nothing happens by default:
        attempt_empty_folder("NON_EXISTENT", ignore_failure=True)
        # but error raised if ignore_failure=True:
        with self.assertRaises(IOError):
            attempt_empty_folder("NON_EXISTENT", ignore_failure=False)

    def test_empty_folder(self):
        folder = self.create_new_dir()
        attempt_empty_folder(folder, ignore_failure=True)
        self.assertTrue(isdir(folder))
        self.assertEqual(os.listdir(folder), [])

    def test_empty_folder_dont_ignore_failures(self):
        folder = self.create_new_dir()
        attempt_empty_folder(folder, ignore_failure=False)
        self.assertTrue(isdir(folder))
        self.assertEqual(os.listdir(folder), [])

    # Utilities ---------------------------------------------------------------

    def create_new_dir(self, num_files=5):
        folder = join(HERE, "temp")
        if isdir(folder):
            rmtree(folder)

        os.makedirs(folder)
        for i in range(num_files):
            with open(join(HERE, "temp", "test_{}.temp".format(i)), "w") as f:
                f.write("BLAH")
        return folder


class TestSyncFolders(TestCase):
    def setUp(self):
        self.source = join(HERE, "test_source_dir")
        self.target = join(HERE, "test_target_dir")

        os.makedirs(self.source)
        self.filelist = ["test_file_{}".format(i) for i in range(10)]
        for fname in self.filelist:
            with open(join(self.source, fname), "w") as f:
                f.write(" ")

        os.makedirs(self.target)

    def tearDown(self):
        if isdir(self.target):
            rmtree(self.target)
        if isdir(self.source):
            rmtree(self.source)

    def test_sync_folders(self):
        self.assertEqual(os.listdir(self.target), [])
        sync_folders(self.source, self.target)
        self.assertEqual(set(os.listdir(self.target)), set(self.filelist))

    def test_sync_folders_white_list(self):
        self.assertEqual(os.listdir(self.target), [])
        sync_folders(self.source, self.target,
                     fname_white_list=self.filelist[:3])
        self.assertEqual(set(os.listdir(self.target)), set(self.filelist[:3]))

    def test_sync_folders_bad_white_list(self):
        with self.assertRaises(IOError):
            sync_folders(self.source, self.target, fname_white_list=["BLAH"])

    def test_sync_folders_black_list(self):
        self.assertEqual(os.listdir(self.target), [])
        sync_folders(self.source, self.target,
                     fname_black_list=[self.filelist[0], self.filelist[-1]])
        self.assertEqual(set(os.listdir(self.target)),
                         set(self.filelist[1:-1]))

    def test_sync_folders_empty_black_list(self):
        self.assertEqual(os.listdir(self.target), [])
        sync_folders(self.source, self.target, fname_black_list=[])
        self.assertEqual(set(os.listdir(self.target)), set(self.filelist))

    def test_sync_folders_long_retry_delay(self):
        self.assertEqual(os.listdir(self.target), [])
        # Local copies so this shouldn't do anything since retries shouldn't be
        # needed:
        sync_folders(self.source, self.target, retry_delay=10)
        self.assertEqual(set(os.listdir(self.target)), set(self.filelist))


@skipIf(NO_GUI, "No GUI backend, likely no X window capabilities.")
class TestOpenFile(TestCase):
    """ Test the ability for the OS to launch a process to open a file.

    Windows only since it uses psutil which is not present on OSX.
    """

    def setUp(self):
        now = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Make the file unique so if the previous test didn't close the
        # application, the next run doesn't collide.
        self.fpath = join(expanduser("~"), "DELETE_ME_{}.txt".format(now))
        with open(self.fpath, "w") as f:
            f.write("DELETE ME")

    def tearDown(self):
        if isfile(self.fpath):
            os.remove(self.fpath)

    def test_open_file(self):
        if not isfile(self.fpath):
            self.skipTest("SOMETHING WENT WRONG WITH THE TestOpenFile TEST!")

        with self.assert_process_created():
            open_file(self.fpath)

    # Utilities ---------------------------------------------------------------

    @contextmanager
    def assert_process_created(self):
        import psutil
        process_list = set(psutil.process_iter())
        yield
        new_process_list = set(psutil.process_iter())
        # If this fails, is it possible that the process opening text files was
        # already open?
        self.assertEqual(len(process_list)+1, len(new_process_list))
        new_proc = (new_process_list - process_list).pop()
        try:
            new_proc.kill()
        except Exception as e:
            print("Failed to kill the created process: error was {}".format(e))
