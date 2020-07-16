from unittest import TestCase
import os
from os.path import isfile

from app_common.traits.assertion_utils import assert_has_traits_almost_equal
from app_common.apptools.preferences import BasePreferenceGroup


class TestPreferencesSerialization(TestCase):
    def setUp(self):
        self.temp_pref_file = "tmp.yaml"

    def tearDown(self):
        if isfile(self.temp_pref_file):
            os.remove(self.temp_pref_file)

    def test_create_save_load(self):
        prefs = PictsViewerPreferences()
        prefs.to_preference_file(self.temp_pref_file)
        new_prefs = Preferences.from_preference_file(
            self.temp_pref_file
        )
        assert_has_traits_almost_equal(prefs, new_prefs)

    def test_create_save_load_custom_app_prefs(self):
        app_preferences = AppPreferenceGroup(console_logging_level=20)
        app_preferences.dirty = False
        prefs = PictsViewerPreferences(app_preferences=app_preferences)
        prefs.to_preference_file(self.temp_pref_file)
        new_prefs = Preferences.from_preference_file(
            self.temp_pref_file
        )
        assert_has_traits_almost_equal(prefs, new_prefs)


class AppPreferenceGroup(BasePreferenceGroup):
    """ Storage for Application related preferences.
    """
    console_logging_level = Int(30)

    def _attrs_to_store_default(self):
        return ["console_logging_level"]


PREFERENCE_CLASS_MAP = {
    "app_preferences": AppPreferenceGroup,
}


class Preferences(BasePreferences):
    """ Drive the loading and saving of preferences for app to/from file
    """
    app_preferences = Instance(AppPreferenceGroup, ())

    #: List of preference types to look for
    _preference_class_map = PREFERENCE_CLASS_MAP

    def _version_default(self):
        return 3

    def _preference_filepath_default(self):
        return "."
