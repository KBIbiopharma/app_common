""" Customization of pyface functionality.
"""
import logging

from pyface.api import DirectoryDialog, FileDialog, OK
from pyface.message_dialog import MessageDialog

local_logger = logging.getLogger(__name__)


def message_dialog(message, title='Error', severity='error'):
    """ Convenience function to show an error message dialog.

    Parameters
    ----------
    message : str
        The text of the message to display.

    title : str
        The text of the dialog title.

    severity : str
        Level of severity for the dialog. One of 'information', 'warning', and
        'error'.
    """
    dialog = MessageDialog(
        parent=None, message=message, title=title, severity=severity
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
            from ...std_lib.filepath_utils import get_home_folder
            return get_home_folder()

    def close(self):
        """ Remember the selected directory.
        """
        super(FileDialogWithMemory, self).close()
        if self.directory:
            FileDialogWithMemory.last_directory = self.directory
            DirectoryDialogWithMemory.last_directory = self.directory


class DirectoryDialogWithMemory(DirectoryDialog):
    """ Customized FileDialog to remember where the last file was loaded from.
    """
    #: Class attribute for all dialogs to share where last file was loaded from
    last_directory = ""

    def _default_directory_default(self):
        if self.last_directory:
            return self.last_directory
        else:
            from ...std_lib.filepath_utils import get_home_folder
            return get_home_folder()

    def close(self):
        """ Remember the selected directory.
        """
        super(DirectoryDialogWithMemory, self).close()
        if self.path:
            DirectoryDialogWithMemory.last_directory = self.path
            FileDialogWithMemory.last_directory = self.path


request_file_docstring_template = \
    """ Request file of type {0} using a pyface file dialog (with memory).

    Parameters
    ----------
    title : str
        Title of the file dialog.

    wildcard_text : str
        Text describing {0} files.

    action : str [OPTIONAL, default='open']
        Type of dialog requested. By default, the action allows to select an
        existing file. Set to 'save as' to create a new file.

    Returns
    -------
    str or None
        Path to the file selected or None if the dialog was cancelled.
    """


def generate_file_requester(file_desc, extension, action='open', title=""):
    """ Convert a file extension into a function prompting user for file path.

    Parameters
    ----------
    file_desc : str
        Description for the file requested.

    extension : str
        Extension of the file requested, for example ".csv" or ".png".

    action : str
        Type of file dialog: open an existing file (default), or 'save as' to
        target a new file.

    Examples
    --------
    >>> # Triggers a dialog asking the user for an existing python file.
    >>> prompter = generate_file_requester("Python", ".py")
    >>> prompter()
    """
    if not title:
        title = "Select {} file name".format(file_desc)
    wildcard_text = "{} files".format(file_desc)

    def request_file(title=title, wildcard_text=wildcard_text, action=action):
        wildcard = FileDialogWithMemory.create_wildcard(wildcard_text,
                                                        "*" + extension)
        file_dialog = FileDialogWithMemory(title=title, wildcard=wildcard,
                                           action=action)
        file_dialog.open()
        if file_dialog.return_code == OK:
            path = file_dialog.path
            # On Windows the dialog doesn't automatically append the extension
            # if missing
            if not path.endswith(extension):
                path += extension
            return path

    request_file.__doc__ = request_file_docstring_template.format(file_desc)
    return request_file


def request_folder(title=""):
    """Request folder using a pyface directory dialog (with memory).

    Parameters
    ----------
    title : str
        Title of the directory dialog.

    Returns
    -------
    str or None
        Returns the path selected for the folder, or None if the dialog was
        aborted.
    """
    if not title:
        title = 'Select folder'

    dialog = DirectoryDialogWithMemory(title=title)
    dialog.open()
    if dialog.return_code == OK:
        return dialog.path


request_python_file = generate_file_requester("Python", ".py")

request_jpeg_file = generate_file_requester("JPEG", ".jpg")

request_png_file = generate_file_requester("PNG", ".png")

request_csv_file = generate_file_requester("CSV", ".csv")

request_excel_file = generate_file_requester("XLSX", ".xlsx")

to_csv_file_requester = generate_file_requester("CSV", ".csv",
                                                action="save as")

to_excel_file_requester = generate_file_requester("XLSX", ".xlsx",
                                                  action="save as")

to_png_file_requester = generate_file_requester("PNG", ".png",
                                                action="save as")

to_jpg_file_requester = generate_file_requester("JPEG", ".jpg",
                                                action="save as")
