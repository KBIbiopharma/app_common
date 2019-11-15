import sys
import traceback
import logging
from os.path import join
from six.moves import input, StringIO
from traceback import format_exc
from contextlib import contextmanager

IS_WINDOWS = sys.platform == 'win32'

IS_OSX = sys.platform == 'darwin'

IS_LINUX = sys.platform.startswith('linux')

logger = logging.getLogger(__name__)


def print_traceback():
    """ Utility to print the active traceback if any.
    """
    _, _, tb = sys.exc_info()
    if tb is not None:
        traceback.print_tb(tb)


def format_tb(limit=10):
    """ Returns the last traceback as a formatted string.

    Parameters
    ----------
    limit : int
        Upper limit to the number of stacks to display in the traceback.
    """
    details = ("\n" + "- Error traceback " + "-" * 61 + "\n" +
               format_exc(limit=limit) + "\n" + "-" * 79)
    return details


def extract_traceback():
    """ Return a formatted string with the last traceback stack trace.
    """
    _, _, tb = sys.exc_info()
    stack_list = traceback.format_list(traceback.extract_tb(tb))
    tb_str = "".join(stack_list)
    return tb_str


def command_line_confirmation(msg, default_value=None):
    """ Prompts the user for a yes/no answer.

    Any result from the user that starts with 'y' is treated as 'Yes'. Anything
    else is treated as False.

    Parameters
    ----------
    msg : str
        Message to prompt the user for the answer. Should specify what the
        default value is if they just hit enter.

    default_value : None or str [OPTIONAL]
        The boolean to return if the user only hits 'Return'. By default, an
        exception is raised if the user doesn't type anything.

    Returns
    -------
    bool
        Whether the users selected 'Yes'.
    """
    res = input(msg)
    if not res:
        if default_value is None:
            msg = "No default specified for this question. Please answer by " \
                  "'yes' or 'no'."
            logger.warning(msg)
            print(msg)
            return command_line_confirmation(msg)
        else:
            res = default_value

    return res.lower()[0] == "y"


@contextmanager
def capture_stdout(stream_name="stdout", steam_close=True):
    """ Capture the stdout temporarily into a StringIO object.

    Parameters
    ----------
    stream_name : str [OPTIONAL, default='stdout']
        Which stream to capture? Values can be 'stdout' or 'stderr'.

    steam_close : bool
        Whether to close the stringIO object. If so, it cannot be read or
        written to once out of the context manager block. If set to False, the
        user code needs to close the stream manually.

    Examples
    --------
    >>> with capture_stdout() as str_io:
            print("FOOBAR")
            assert("FOOBAR\n" == str_io.getvalue())

    >>> with capture_stdout(io_close=False) as str_io:
            print("FOOBAR")
    >>> print(str_io.getvalue())
    FOOBAR
    >>> str_io.close()
    """
    # setup the environment
    backup = getattr(sys, stream_name)
    setattr(sys, stream_name, StringIO())
    try:
        yield getattr(sys, stream_name)
    finally:
        setattr(sys, stream_name, backup)
        if steam_close:
            # If close the stream, cannot ask for the value after this
            getattr(sys, stream_name).close()


def _bin_folder_name():
    """ Returns the name of the bin/Scripts folder in active python.
    """
    if IS_WINDOWS:
        folder = "Scripts"
    else:
        folder = "bin"
    return folder


def get_bin_folder():
    """ Returns path to bin directory of active python.
    """
    bin_dir_name = _bin_folder_name()
    bin_dir = join(sys.prefix, bin_dir_name)
    return bin_dir
