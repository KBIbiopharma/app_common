""" Customization of pyface functionality.
"""
import logging

from traits.api import Bool
from pyface.api import FileDialog
from pyface.action.api import Action
from pyface.tasks.action.task_action import TaskAction
from pyface.message_dialog import MessageDialog
from apptools.undo.action.api import UndoAction, RedoAction

from app_common.pyface.logging_utils import action_monitoring

local_logger = logging.getLogger(__name__)

KNOWN_SEVERITIES = ['information', 'warning', 'error']


class MonitoredAction(Action):
    """ Modified pyface action to record `perform` requests & handle exceptions.
    """
    allow_gui = Bool(True)

    def perform(self, event):
        with action_monitoring(self.name, allow_gui=self.allow_gui):
            super(MonitoredAction, self).perform(event)


class MonitoredUndoAction(MonitoredAction, UndoAction):
    """ Modified pyface undo action to record `perform` requests & handle
    exceptions.
    """
    pass


class MonitoredRedoAction(MonitoredAction, RedoAction):
    """ Modified pyface redo action to record `perform` requests & handle
    exceptions.
    """
    pass


class MonitoredTaskAction(TaskAction):
    """ Modified pyface task action to record `perform` requests & handle
    exceptions.
    """
    allow_gui = Bool(True)

    def perform(self, event=None):
        with action_monitoring(self.name, allow_gui=self.allow_gui):
            super(MonitoredTaskAction, self).perform(event)


def message_dialog(parent, message, title='Error', severity='error'):
    """ Convenience function to show an error message dialog.

    Parameters
    ----------
    parent : toolkit control or None
        The toolkit control that should be the parent of the dialog.
    message : str
        The text of the message to display.
    title : str
        The text of the dialog title.
    severity : str
        Level of severity for the dialog. One of 'information', 'warning', and
        'error'.
    """
    dialog = MessageDialog(
        parent=parent, message=message, title=title, severity=severity
    )
    dialog.open()

    return


class FileDialogWithMemory(FileDialog):
    """ Customized FileDialog to remember where the last file was loaded from.
    """
    #: Class attribute for all dialogs to share where last file was loaded from
    last_directory = ""

    def _default_directory_default(self):
        if self.last_directory:
            return self.last_directory
        else:
            from ..std_lib.filepath_utils import get_home_folder
            return get_home_folder()

    def close(self):
        """ Remember the directory the file was loaded from/saved to.
        """
        super(FileDialogWithMemory, self).close()
        if self.directory:
            FileDialogWithMemory.last_directory = self.directory
