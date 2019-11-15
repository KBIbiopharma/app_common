""" UI to select a python script to run inside Reveal-Chromatography.
"""
import logging
import os
from os.path import basename, dirname, isdir, isfile, join, splitext

from pyface.api import confirm, NO
from traits.api import Bool, Button, Code, Directory, Enum, HasStrictTraits, \
    List, Str
from traitsui.api import HGroup, Item, Label, OKCancelButtons, VGroup, View

from app_common.std_lib.file_ext import is_py_file
from app_common.pyface.ui.extra_file_dialogs import request_python_file

logger = logging.getLogger(__name__)

DEFAULT_SCRIPT_NAME = "Create new"

DEFAULT_NEW_SCRIPT_NAME = "Script 0"


class PythonScriptFileSelector(HasStrictTraits):
    """ GUI to select or create a Python script.

    This selector allows to select scripts that were saved in the default
    location (defaults to app_folder/python_scripts), load any python file,
    save a copy of it in the default location, or simply create new python
    scripts with custom code, and allow it to be saved as a script in the
    default location.

    NOTE: a script can be modified before returning, so there is no guaranty
    that the filepath and the code are sync-ed.
    """

    #: Default location on the file system to look for scripts
    default_location = Directory

    #: Location for (sample) scripts that ship with the software
    sample_script_location = Directory

    #: Script path
    filepath = Str

    #: Button to launch a file dialog and set filepath
    filepath_selector_button = Button("Select a python file...")

    #: Script name
    name = Enum(values="known_scripts")

    #: List of script names found in the default script location
    known_scripts = List(Str)

    #: Script content
    code = Code

    #: Is the code content different from the filepath content?
    dirty = Bool

    #: Button to save the current code
    save_script_as_button = Button("Save as...")

    save_button = Button("Save")

    reload_button = Button("Reload script")

    #: Whether or not the selected script is in the default location
    is_in_default_location = Bool(True)

    def traits_view(self):
        view = View(
            VGroup(
                Label("Select a pre-defined script, load a custom one from any"
                      " python file or type in custom code below."),
                HGroup(
                    Item("name", label="Script name"),
                    Item("filepath_selector_button", show_label=False),
                    Item("filepath", springy=True, style="readonly")
                ),
                VGroup(
                    Item("code", show_label=False),
                    HGroup(
                        Item("save_script_as_button", show_label=False,
                             enabled_when="dirty and code"),
                        Item("save_button", show_label=False,
                             enabled_when="dirty and code and name"),
                        Item("reload_button", show_label=False)
                    ),
                    label="Script Content", show_border=True
                ),
            ),
            title="Select a python script",
            resizable=True,
            buttons=OKCancelButtons,
            width=600
        )
        return view

    def create_new_script(self, target_name, filepath=None):
        """ Create a new script file, placed in the user's default location.

        Once created, the dirty flag, filepath, and name attributes are set as
        appropriate.

        Parameters
        ----------
        target_name : str
            Name of the future script.

        filepath : str
            Full filepath to the script file to write.
        """
        if not filepath:
            filepath = self._filepath_from_script_name(target_name)

        with open(filepath, "w") as f:
            f.write(self.code)

        if target_name not in self.known_scripts:
            self.known_scripts.append(target_name)

        self.filepath = filepath
        self.name = target_name
        self.dirty = False

    # Trait listeners ---------------------------------------------------------

    def _filepath_selector_button_fired(self):
        path = request_python_file()
        if path:
            self.filepath = path

    def _name_changed(self, new):
        if new == DEFAULT_SCRIPT_NAME:
            self.filepath = ""
        else:
            attempt = self._filepath_from_script_name(new)
            if isfile(attempt):
                self.filepath = attempt
            else:
                self.filepath = self._filepath_from_script_name(
                    new, self.sample_script_location
                )

    def _filepath_changed(self):
        if self._validate():
            self.is_in_default_location = (dirname(self.filepath) ==
                                           self.default_location)
            target_name = self._script_name_from_filepath(self.filepath)
            self.code = open(self.filepath).read()
            if self.is_in_default_location:
                # A valid user script was selected
                self.name = target_name
                self.dirty = False
            elif dirname(self.filepath) == self.sample_script_location:
                # A valid sample script was selected. Dirty to allow user to
                # save it in default location.
                self.name = target_name
                self.dirty = True
            else:
                # A general python file was selected. Reset script name and
                # allow to save it in default location.
                self.name = DEFAULT_SCRIPT_NAME
                self.dirty = True
        else:
            self.is_in_default_location = False
            self.name = DEFAULT_SCRIPT_NAME
            self.code = ""
            self.dirty = False

    def _save_script_as_button_fired(self):
        target_name = self._prompt_for_script_name()
        if target_name is None:
            return

        if not isdir(self.default_location):
            os.mkdir(self.default_location)

        filepath = self._filepath_from_script_name(target_name)
        if isfile(filepath):
            msg = "A script with name {} already exists. Overwrite?"
            msg = msg.format(target_name)
            result = confirm(None, msg)
            if result == NO:
                return

        self.create_new_script(target_name)

    def _save_button_fired(self):
        if not isdir(self.default_location):
            os.mkdir(self.default_location)

        if self.is_in_default_location:
            filepath = None
        else:
            filepath = self.filepath

        self.create_new_script(self.name, filepath)

    def _reload_button_fired(self):
        self._filepath_changed()

    def _code_changed(self):
        self.dirty = True

    def _default_location_changed(self):
        self.known_scripts = self._build_known_scripts_from_default_loc()
        self.name = DEFAULT_SCRIPT_NAME

    # Private methods ---------------------------------------------------------

    def _validate(self, filepath=None):
        if filepath is None:
            filepath = self.filepath

        return splitext(basename(filepath))[1] == ".py" and isfile(filepath)

    def _prompt_for_script_name(self):
        prompter = _ScriptNamePrompter()
        ui = prompter.edit_traits(kind="modal")
        if not ui.result:
            return None
        else:
            return prompter.target_name.strip()

    def _filepath_from_script_name(self, target_name, dirpath=None):
        """ Build the filepath from a script name.

        Parameters
        ----------
        target_name : str
            Script name to build the path of.

        dirpath : str
            Target directory to place the file. Defaults to
            self.default_location.

        Returns
        -------
        str
            File path of the script.
        """
        if dirpath is None:
            dirpath = self.default_location
        return join(dirpath, target_name + ".py")

    def _script_name_from_filepath(self, filepath):
        return splitext(basename(filepath))[0]

    def _build_known_scripts_from_default_loc(self):
        if not isdir(self.default_location):
            os.mkdir(self.default_location)

        user_scripts = self._all_scripts_from_dir(self.default_location)
        sample_scripts = self._all_scripts_from_dir(
            self.sample_script_location
        )
        sample_scripts = list(set(sample_scripts) - set(user_scripts))
        all_scripts = [DEFAULT_SCRIPT_NAME] + sorted(user_scripts) + \
            sorted(sample_scripts)
        return all_scripts

    def _all_scripts_from_dir(self, directory):
        """ Extract all scripts found in a directory.
        """
        if not isdir(directory):
            return []

        def name_from_filename(filename):
            return self._script_name_from_filepath(join(self.default_location,
                                                        filename))

        # skip __init__.py file to make it easier for people to make that
        # location a python package without seeing that file.
        return [name_from_filename(filename)
                for filename in os.listdir(directory)
                if is_py_file(filename) and filename != "__init__.py"]

    # Trait initialization methods --------------------------------------------

    def _known_scripts_default(self):
        return self._build_known_scripts_from_default_loc()


class _ScriptNamePrompter(HasStrictTraits):
    """ Quick UI for prompting the user to specify a script name.
    """
    target_name = Str(DEFAULT_NEW_SCRIPT_NAME)
    view = View(
        Item("target_name", springy=True,
             tooltip="Alphanumeric characters only"),
        width=200, resizable=True, buttons=OKCancelButtons,
        title="Select a script name"
    )


if __name__ == "__main__":
    sel = PythonScriptFileSelector()
    sel.configure_traits()
