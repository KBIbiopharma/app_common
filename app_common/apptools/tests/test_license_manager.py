from unittest import skipIf, TestCase
import os

from app_common.apptools.testing_utils import temp_bringup_ui_for
from app_common.apptools.license_manager import LicenseKey

skip = os.environ.get("ETS_TOOLKIT", "qt4") == "null"


@skipIf(skip, "No GUI toolkit to paint into.")
class TestLicenseKey(TestCase):
    def test_bring_up(self):
        with temp_bringup_ui_for(LicenseKey()):
            pass
