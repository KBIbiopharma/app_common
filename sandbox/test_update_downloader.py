""" For model tests, see downstream project repositories.
"""
from unittest import skipIf, TestCase
from os.path import dirname, isfile, join
import os
from zipfile import is_zipfile

skip = (os.environ.get("ETS_TOOLKIT", "qt4") == "null")

if not skip:
    from app_common.apptools.update_downloader import retrieve_file_from_url, \
        UpdateDownloader, version_str_to_version, version_to_version_str

CONTENT_FNAME = 'content_0.7.2_3.json'

RELEASE_ENTRY = {u'release_filenames': [CONTENT_FNAME],
                 u'target_versions': u'0.6..+',
                 u'target_builds': u'.+',
                 u'target_users': u'all'}

HERE = dirname(__file__)


@skipIf(skip, "No UI backend to paint UIs into.")
class TestUpdateDownloaderGUI(TestCase):
    def test_bring_up(self):
        from app_common.apptools.testing_utils import temp_bringup_ui_for

        downloader = UpdateDownloader(current_version=("0.1.0", 1))
        with temp_bringup_ui_for(downloader):
            pass


@skipIf(skip, "No UI backend to paint UIs into.")
class TestVersionStrVersionTuple(TestCase):
    def test_version_str_to_version(self):
        self.assertEqual(version_str_to_version("0.1.2"), (0, 1, 2))
        self.assertEqual(version_str_to_version("0.1.2.dev0"),
                         (0, 1, 2, "dev0"))

    def test_version_to_version_str(self):
        self.assertEqual(version_to_version_str((0, 1, 2)), "0.1.2")
        self.assertEqual(version_to_version_str((0, 1, 2, "dev0")),
                         "0.1.2.dev0")


@skipIf(skip, "No UI backend to paint UIs into.")
class TestUpdaterVersionDisplay(TestCase):
    def setUp(self):
        self.updater = UpdateDownloader(current_version=("0.6.2", 1))

    def test_display_current_version(self):
        v = self.updater.current_version
        version, build = v
        self.assertEqual(version, (0, 6, 2))
        self.assertEqual(build, 1)
        self.assertEqual(self.updater.current_version_msg,
                         "0.6.2 (build: 1)")

    def test_display_release_version(self):
        self.updater.release_data = [RELEASE_ENTRY]
        self.assertEqual(self.updater.newest_release_msg,
                         "0.7.2 (build: 3)")


@skipIf(skip, "No UI backend to paint UIs into.")
class TestUpdaterGetReleaseVersion(TestCase):
    def setUp(self):
        self.updater = UpdateDownloader()

    def test_get_release_version(self):
        v = self.updater.get_release_version(CONTENT_FNAME)
        version = v[:-1]
        build = v[-1]
        self.assertEqual(version, (0, 7, 2))
        self.assertEqual(build, 3)

    def test_get_release_version_bad_file(self):
        with self.assertRaises(ValueError):
            self.updater.get_release_version("BADFILE_NAME")

    def test_get_release_version_wrong_extension(self):
        with self.assertRaises(ValueError):
            self.updater.get_release_version('content_0.7.2_3.text')


@skipIf(skip, "No UI backend to paint UIs into.")
class TestUpdaterGetUserMatch(TestCase):
    def setUp(self):
        self.updater = UpdateDownloader()

    def test_get_user_match_all_users(self):
        pattern = ".+"
        self.assertTrue(self.updater.get_user_match(pattern))

    def test_get_user_match_all_users_old_style(self):
        pattern = "all"
        self.assertTrue(self.updater.get_user_match(pattern))

    def test_no_match(self):
        pattern = "UNKNOWN_PATTERN"
        self.assertFalse(self.updater.get_user_match(pattern))


@skipIf(skip, "No UI backend to paint UIs into.")
class TestFileDownloadUtility(TestCase):

    def tearDown(self):
        if isfile(self.tgt_file):
            os.remove(self.tgt_file)

    def test_retrieve_egg_file(self):
        self.tgt_file = join(HERE, "new_file.egg")
        if isfile(self.tgt_file):
            os.remove(self.tgt_file)

        # Link to egg file for app_updater 0.3.0:
        egg_url = "https://mycloud.kbibiopharma.com/index.php/s/QMUOdTjR1Jvtc9A/download"  # noqa
        retrieve_file_from_url(egg_url, self.tgt_file)
        self.assertTrue(isfile(self.tgt_file))
        # An egg is a zipfile:
        self.assertTrue(is_zipfile(self.tgt_file))
