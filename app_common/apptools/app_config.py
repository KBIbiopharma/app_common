import logging

import sys
import os
from os.path import abspath, expanduser, join

from app_common.std_lib.filepath_utils import string2filename

IS_WINDOWS = sys.platform == "win32"


def base_get_app_folder(app_title, app_family=None):
    """ Returns an absolute path on the current system where the current user
    should have write rights.

    Tested on Windows 7, Windows 10 and OSX.

    Parameters
    ----------
    app_title : str
        Name of the application to find the application folder for.

    app_family : str [OPTIONAL]
        Optional name of a family of applications the application is part of,
        so their data is grouped within a family folder.
    """
    logger = logging.getLogger(__name__)

    if IS_WINDOWS:
        path_elements = [string2filename(app_title.capitalize())]
        if app_family:
            path_elements = [string2filename(app_family.capitalize())] + \
                path_elements
        if 'APPDATA' in os.environ:
            path = join(os.environ["APPDATA"], *path_elements)
        elif 'LOCALAPPDATA' in os.environ:
            path = join(os.environ["LOCALAPPDATA"], *path_elements)
        else:
            msg = "Failed to find the application folder: neither APPDATA nor"\
                  " LOCALAPPDATA were found in the environment variables."
            logger.exception(msg)
            raise ValueError(msg)
    else:
        # OSX and Posix system to store logs in the home directory, and make
        # paths be all lower case:
        path_elements = [string2filename(app_title.lower())]
        if app_family:
            path_elements = [string2filename(app_family.lower())] + \
                path_elements

        path = join(expanduser('~'), "." + path_elements[0],
                    *path_elements[1:])

    return abspath(path)
