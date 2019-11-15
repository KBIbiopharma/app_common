import sys
import logging
import getpass

from .sys_utils import IS_LINUX, IS_OSX, IS_WINDOWS

logger = logging.getLogger(__name__)

UNKNOWN_UNAME = "Unknown user"


def get_ctrl():
    """ Return the name of the control key based on the current platform.
    """
    if IS_WINDOWS or IS_LINUX:
        ctrl = "ctrl"
    elif IS_OSX:
        ctrl = "cmd"
    else:
        msg = "Platform {} not supported.".format(sys.platform)
        logger.exception(msg)
        raise NotImplementedError(msg)
    return ctrl


def collect_user_name():
    """ Returns the username as provided by the OS. Returns a constant if it
    fails.
    """
    try:
        uname = getpass.getuser()
    except Exception as e:
        logger = logging.getLogger(__name__)
        msg = "Failed to collect the user name: error was {}.".format(e)
        logger.warning(msg)
        uname = UNKNOWN_UNAME

    return uname
