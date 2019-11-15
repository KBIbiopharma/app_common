from unittest import TestCase

from app_common.std_lib.os_utils import collect_user_name, UNKNOWN_UNAME


class TestUsername(TestCase):
    def test_collect_user_name(self):
        uname = collect_user_name()
        self.assertIsInstance(uname, str)
        self.assertNotEqual(uname, UNKNOWN_UNAME)
