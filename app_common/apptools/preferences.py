""" Base classes for storing preferences to file, and displaying in UI.
"""
import logging
import yaml
from os.path import abspath

from traits.api import Bool, HasStrictTraits, HasTraits, Int, List, Property, \
    Str

DEFAULT_PREFERENCE_FILENAME = "preferences.yaml"

logger = logging.getLogger(__name__)


class BasePreferenceGroup(HasTraits):
    """ Base class for a group of Preferences.

    Note: These classes are HasTraits as opposed to HasStrictTraits so that
    they are flexible, and allow for attribute removal.
    """
    #: Flag to flip when preferences have been changed
    dirty = Bool

    #: List of attribute names that should be stored in the file
    attrs_to_store = List

    def _anytrait_changed(self, name, old, new):
        if name in self.attrs_to_store and not self.dirty:
            self.dirty = True

    def to_data(self):
        data = {}
        for attr_name in self.attrs_to_store:
            data[attr_name] = getattr(self, attr_name)
        return data


class BasePreferences(HasStrictTraits):
    """ Base class to loading and save application preferences to/from file.
    """
    #: File path to store the preferences in
    preference_filepath = Str

    #: Mapping between preference type name and the instance to build from it
    _preference_class_map = {}

    #: Map preference versions -> functions to transform pref data upon loading
    _preference_alteration_funcs = {}

    #: Flag to flip when preferences have been changed
    dirty = Property(Bool)

    #: Version of the preferences
    version = Int

    @classmethod
    def from_preference_file(cls, pref_filepath):
        """ Create a Preference instance from a preference file.
        """
        with open(pref_filepath, "r") as pref_file:
            data = yaml.load(pref_file, Loader=yaml.FullLoader)
            loaded_version = data["version"]

        preferences_traits = {}
        for preference_type in cls._preference_class_map.keys():
            preference_data = data.get(preference_type, {})
            klass = cls._preference_class_map[preference_type]
            preferences_traits[preference_type] = klass(**preference_data)

        prefs = cls(**preferences_traits)
        prefs.version = loaded_version

        # Transformation needed?
        if loaded_version in cls._preference_alteration_funcs:
            prefs = cls._preference_alteration_funcs[loaded_version](prefs)

        prefs.dirty = False
        return prefs

    def to_preference_file(self, target_file=None):
        """ Store current preferences to file.
        """
        if target_file is None:
            target_file = self.preference_filepath

        data = {"version": self.version}
        for preference_type in self._preference_class_map.keys():
            data[preference_type] = getattr(self, preference_type).to_data()

        logger.debug("Storing preferences to {}".format(abspath(target_file)))
        with open(target_file, "w") as pref_file:
            yaml.dump(data, pref_file, default_flow_style=False, indent=4)

    def _preference_filepath_default(self):
        return DEFAULT_PREFERENCE_FILENAME

    def _set_dirty(self, value):
        for group_name in self._preference_class_map.keys():
            group = getattr(self, group_name)
            group.dirty = value

    def _get_dirty(self):
        for group_name in self._preference_class_map.keys():
            group = getattr(self, group_name)
            if group.dirty:
                return True

        return False
