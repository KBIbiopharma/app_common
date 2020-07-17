from unittest import TestCase
import os
from os.path import isfile
import yaml

from traits.api import Instance, Int, List
from traits.trait_handlers import TraitListObject

from app_common.traits.assertion_utils import assert_has_traits_almost_equal
from app_common.apptools.preferences import BasePreferenceGroup, \
    BasePreferences


class TestPreferencesSerialization(TestCase):
    def setUp(self):
        self.temp_pref_file = "tmp.yaml"

    def tearDown(self):
        if isfile(self.temp_pref_file):
            os.remove(self.temp_pref_file)

    def test_create_save_load(self):
        prefs = Preferences()
        prefs.to_preference_file(self.temp_pref_file)
        new_prefs = Preferences.from_preference_file(
            self.temp_pref_file
        )
        assert_has_traits_almost_equal(prefs, new_prefs)

    def test_create_save_load_custom_app_prefs(self):
        app_preferences = AppPreferenceGroup(console_logging_level=20)
        app_preferences.dirty = False
        prefs = Preferences(app_preferences=app_preferences)
        prefs.to_preference_file(self.temp_pref_file)
        new_prefs = Preferences.from_preference_file(
            self.temp_pref_file
        )
        assert_has_traits_almost_equal(prefs, new_prefs)

    def test_create_save_load_no_trait_types(self):
        app_preferences = AppPreferenceGroup(recent_files=["foo.txt",
                                                           "bar.csv"])
        app_preferences.dirty = False
        prefs = Preferences(app_preferences=app_preferences)
        prefs.to_preference_file(self.temp_pref_file)
        new_prefs = Preferences.from_preference_file(
            self.temp_pref_file
        )
        assert_has_traits_almost_equal(prefs, new_prefs)

        self.assertIsInstance(prefs.app_preferences.recent_files,
                              TraitListObject)
        # Make sure what was serialized was a python list:
        with open(self.temp_pref_file) as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        recent_files = data['app_preferences']['recent_files']
        self.assertIsInstance(recent_files, list)


class AppPreferenceGroup(BasePreferenceGroup):
    """ Storage for Application related preferences.
    """
    console_logging_level = Int(30)

    recent_files = List

    def _attrs_to_store_default(self):
        return ["console_logging_level", "recent_files"]


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
