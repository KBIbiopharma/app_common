from __future__ import print_function
import sys
import os
from os.path import abspath, expanduser, isdir, isfile, join, split, splitext
import logging
from subprocess import Popen
from shutil import copy

from .command_line_tools import try_action
from .str_utils import add_suffix_if_exists
from .sys_utils import IS_LINUX, IS_OSX, IS_WINDOWS

SPECIAL_CHARACTERS = " \\/:;()[]{}%^$*#@!+=-&|<>?\"'"

logger = logging.getLogger(__name__)


def string2filename(string, special_chars=SPECIAL_CHARACTERS, adl_chars="",
                    replace_with="_"):
    """ Sanitize a string, removing special characters to make it a valid
    filename.

    TODO: what to do with non-ascii characters?

    Parameters
    ----------
    string : str
        String to transform into a valid filename.

    special_chars : str [OPTIONAL, default=" \\/:()[]{}%^$*#@!+=-\"'"]
        All characters to be replaced by a

    adl_chars : str [OPTIONAL]
        Characters to be added to the special_chars, to be replaced by an
        underscore.

    replace_with : str [OPTIONAL, default="_"]
        Character to replace all special characters by.
    """
    # remove any non-ascii characters?
    # string = string.encode('ascii', 'ignore').strip()

    # Replace all special characters with '_':
    for char in set(special_chars+adl_chars):
        string = string.replace(char, replace_with)

    # Remove all double underscores:
    while replace_with*2 in string:
        string = string.replace(replace_with*2, replace_with)

    # Remove trailing underscore if any:
    if string.endswith(replace_with):
        string = string[:-1]

    if string.startswith(replace_with):
        string = string[1:]

    return string


def rotate_filename(candidate_filepath, suffix_base="_v{}"):
    """ Append and rotate the suffix of a filename until it doesn't collide
    with other files in the same folder.

    Parameters
    ----------
    candidate_filepath : str
        Path to the future file if it doesn't already exist.

    suffix_base : str
        Suffix formatting string to use to append to the basename to make it
        rotate until it doesn't exist.
    """
    dir_path, candidate_filename = split(candidate_filepath)
    init_name, candidate_ext = splitext(candidate_filename)
    existing_names = []
    for fname in os.listdir(dir_path):
        name, ext = splitext(fname)
        if ext == candidate_ext:
            existing_names.append(name)

    final_name = add_suffix_if_exists(init_name, existing_names,
                                      suffix_patt=suffix_base)
    return join(dir_path, final_name + candidate_ext)


def attempt_remove_file(filepath, ignore_failure=True, verbose=True):
    """ Attempts to delete an existing file.

    Parameters
    ----------
    filepath : str
        Path to the file that should be deleted.

    ignore_failure : bool
        Whether to just log any error that occur when trying to delete the
        file, rather than raise it.

    verbose : bool [OPTIONAL, default=True]
        Whether to log debug messages.

    Returns
    -------
    bool
        Whether the requested path was deleted.

    Raises
    ------
    IOError
        If the path provided isn't a file. That likely means that it either
        doesn't exist, or is a folder.
    """
    if isfile(filepath):
        try:
            os.remove(filepath)
            if verbose:
                logger.debug("{} deleted.".format(filepath))
            return True
        except Exception as e:
            msg = "Failed to delete {}. Error was {}".format(filepath, e)
            if ignore_failure:
                logger.debug(msg)
                return False
            else:
                logger.exception(msg)
                raise
    else:
        msg = "Path to {} isn't a file or doesn't exist!".format(filepath)
        logger.exception(msg)
        raise IOError(msg)


def attempt_empty_folder(path, description="", ignore_failure=True):
    """ Delete the content of a filesystem path.

    Note: this function doesn't use the logging module because it might be used
    to delete the folder of logging files.

    Parameters
    ----------
    path : str
        Path to empty.

    description : str
        Description of the content of the path (for messaging).

    ignore_failure : bool
        Set to False to raise exceptions if folder not found, or file fails to
        be deleted.
    """
    if not isdir(path):
        msg = "Unable to empty {}: folder doesn't exist".format(path)
        if ignore_failure:
            logger.error(msg)
            return
        else:
            raise IOError(msg)

    filemames_to_delete = os.listdir(path)
    size_to_delete = sum(os.path.getsize(join(path, f))
                         for f in filemames_to_delete)
    size_to_delete /= 1.e6
    num_files_to_delete = len(filemames_to_delete)
    msg = "Deleting {} {} from {}. That will free {:.2f} MB."
    msg = msg.format(num_files_to_delete, description, path, size_to_delete)
    logger.info(msg)
    for filename in os.listdir(path):
        filepath = join(path, filename)
        attempt_remove_file(filepath, ignore_failure=ignore_failure,
                            verbose=False)


def get_home_folder():
    """ Returns an absolute path on the current system Home folder.

    Note: Tested on Windows 7 (and OSX) only but should work on Windows 10 too.
    """
    return abspath(expanduser('~'))


def open_file(file_path):
    """ Launch default application to open provided file.

    Parameters
    ----------
    file_path: str
        Path to the file the function will open.

    Returns
    -------
    None or Process
        Returns None on Windows, and the created process on Linux and OSX.
    """
    if IS_WINDOWS:
        from os import startfile
        startfile(file_path)
    elif IS_OSX:
        proc = Popen(["open", file_path])
        return proc
    elif IS_LINUX:
        try:
            proc = Popen(["xdg-open", file_path])
            return proc
        except OSError as e:
            msg = "xdg-open command failed with the following error: {}."
            msg = msg.format(e)
            logger.exception(msg)
            return
    else:
        msg = "Operation not implemented on {}.".format(sys.platform)
        logger.exception(msg)
        raise NotImplementedError(msg)


def sync_folders(source_dir, target_dir, fname_white_list=None,
                 fname_black_list=None, retry_delay=1):
    """ Recursively copy files from a source to a target. Retry on failure.
    """
    if not isdir(source_dir):
        msg = "Source folder {} doesn't exist or isn't visible."
        logger.exception(msg)
        IOError(msg)

    if not isdir(target_dir):
        with try_action("create target dir", retry_delay=retry_delay):
            os.makedirs(target_dir)

    source_content = set(os.listdir(source_dir))
    if fname_white_list is None:
        fname_white_list = source_content
    else:
        missing = set(fname_white_list) - source_content
        if missing:
            msg = "White list contains files that are not in the source " \
                  "directory: {}".format(missing)
            logger.exception(msg)
            raise IOError(msg)

    if fname_black_list:
        fname_list = set(fname_white_list) - set(fname_black_list)
    else:
        fname_list = fname_white_list

    with try_action("list content of target dir", retry_delay=retry_delay):
        target_content = set(os.listdir(target_dir))

    for fname in fname_list:
        if fname in target_content:
            continue

        # Cheap progress bar:
        print(".", end="")
        with try_action("copy {}".format(fname), retry_delay=retry_delay):
            copy(join(source_dir, fname), join(target_dir, fname))
