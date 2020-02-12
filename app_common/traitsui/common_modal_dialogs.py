""" Functions to pop up dialogs to request data from users.
"""
import logging

from traits.api import Any, Bool, Dict, Either, Enum, Float, HasStrictTraits, \
    List, Set, Str
from traitsui.api import EnumEditor, Item, OKCancelButtons, View

from .text_with_validation_editors import TextEditor, \
    TextWithExcludedValuesEditor
from .common_traitsui_groups import make_window_title_group

logger = logging.getLogger(__name__)


def request_string(default_str_value="", dlg_kind="livemodal", dlg_klass=None,
                   **dlg_traits):
    """ Utility to request the user a string, by popping up a modal dialog.

    Parameters
    ----------
    default_str_value : str [OPTIONAL]
        Value to display by default. Ignored if :arg:`dlg_klass` is provided.

    dlg_kind : str or None [OPTIONAL]
        Kind value passed to edit_traits. Mostly for testing purposes, leave as
        default in normal use.

    dlg_klass : type [OPTIONAL]
        Class to use to request the string. Leave empty to use the default
        requester class.

    **dlg_traits : dict
        Traits for the dialog class. Use to specify the window width, title,
        view subclass, or forbidden values.

    Returns
    -------
    unicode
        String to add or None if the dialog is cancelled.
    """

    if dlg_klass is None:
        dlg_klass = StrRequesterDlg

    dlg_traits["str_to_add"] = default_str_value
    dlg = dlg_klass(**dlg_traits)
    ui = dlg.edit_traits(kind=dlg_kind)
    if ui.result:
        return dlg.str_to_add
    else:
        msg = "String request dialog cancelled by user."
        logger.debug(msg)
        # Return the ui object for testing/introspection purposes
        return ui


def request_string_selection(string_options, dlg_kind="livemodal",
                             dlg_klass=None, **selector_traits):
    """ Dialog to select a string among a list of options.

    Parameters
    ----------
    string_options : list
        List of string values to choose from. Passed as the `string_options`
        attribute of the selector dialog (`dlg_klass` or `GuiStringSelector`).

    dlg_kind : str or None [OPTIONAL]
        Kind of dialog to open for user to interact with. Mostly for testing
        purposes, leave as default in normal use.

    dlg_klass : class [OPTIONAL]
        Class to use to create and display the dialog. Leave as None to use the
        default StringSelector.

    **selector_traits : dict [OPTIONAL]
        Additional traits to control the behavior and initialization of the
        `Selector` object, for example `title`, `selected_string`, `view_klass`
        or view controls.

    Returns
    -------
    str or None
        Returns the selected string if selection dialog not cancelled. None
        otherwise.
    """
    if dlg_klass is None:
        dlg_klass = GuiStringSelector

    selector_traits["string_options"] = string_options

    # pop out to handle after creation and after some checks:
    selected_string = selector_traits.pop("selected_string", "")

    chooser = dlg_klass(**selector_traits)

    if selected_string:
        if selected_string in chooser.string_options:
            chooser.selected_string = selected_string
        else:
            msg = "Default value wasn't in the list of options. Skipping."
            logger.warning(msg)

    ui = chooser.edit_traits(kind=dlg_kind)
    if ui.result:
        return chooser.selected_string
    else:
        msg = "String selection dialog cancelled by user."
        logger.debug(msg)
        # Return the ui object for testing/introspection purposes
        return ui


# Helper classes --------------------------------------------------------------

class BaseDlg(HasStrictTraits):
    """ Base class to controlling a user dialog.
    """
    #: Whether to include the title as text at the top of the view
    include_title_group = Bool(True)

    #: Title of the window and optionally the title text at the top of the view
    title = Str

    #: Provide a subclass of the traitsui.View for app customizations (icon, ...)  # noqa
    view_klass = Any(View)

    #: Control the width
    view_width = Float(-1)


class StrRequesterDlg(BaseDlg):
    """ Class to support requesting a string from the user.
    """
    #: String to be typed by the user and returned
    str_to_add = Str

    #: List of values the string isn't allowed to be
    forbidden_values = Either(Set, List)

    #: Optional additional traits to control the TextEditor
    editor_traits = Dict

    def traits_view(self):
        if self.forbidden_values:
            editor = TextWithExcludedValuesEditor(
                forbidden_values=self.forbidden_values, **self.editor_traits)
        else:
            editor = TextEditor(**self.editor_traits)

        groups = [Item("str_to_add", width=self.view_width, show_label=False,
                       editor=editor)]
        if self.include_title_group:
            groups.insert(0, make_window_title_group(title=self.title))

        kw = {"title": self.title, "buttons": OKCancelButtons}
        view = self.view_klass(*groups, **kw)
        return view

    def _view_width_default(self):
        return 500


class GuiStringSelector(BaseDlg):
    """ General string chooser.
    """
    string_options = List(Str)

    selected_string = Str

    show_label = Bool

    label = Str("Selected string")

    ui_mode = Enum(["enum"])

    def traits_view(self):
        if self.ui_mode == "enum":
            item = Item("selected_string", width=self.view_width,
                        editor=EnumEditor(name='string_options'),
                        show_label=self.show_label, label=self.label)
        else:
            msg = "Known modes are: 'enum' but {} was provided.".format(
                self.ui_mode)
            logger.exception(msg)
            raise ValueError(msg)

        groups = [item]
        if self.include_title_group:
            groups.insert(0, make_window_title_group(title=self.title))

        view = self.view_klass(
            *groups,
            title=self.title,
            buttons=OKCancelButtons
        )
        return view

    def _show_label_default(self):
        return bool(self.label)
