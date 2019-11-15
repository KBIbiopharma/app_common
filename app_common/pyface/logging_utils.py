import logging
from contextlib import contextmanager

from ..std_lib.sys_utils import format_tb

local_logger = logging.getLogger(__name__)

KNOWN_SEVERITIES = ['information', 'warning', 'error']


def get_log_file(log_folder=""):
    """ Returns path to root logger log file if one found.

    If none is found, it returns a string pointing to the log folder.
    """
    default = "in {}".format(log_folder)
    try:
        master_logger = logging.getLogger()
        for handler in master_logger.handlers:
            if isinstance(handler, logging.FileHandler):
                return handler.baseFilename
        return default
    except Exception as e:
        msg = "Failed to retrieve the logger's filename. Error was {}"
        local_logger.warning(msg.format(e))
        return default


@contextmanager
def action_monitoring(action_name, log_folder="", logger=None, allow_gui=True,
                      gui_title='Error', gui_severity='error',
                      feedback_menu_name="Help > Submit feedback/Report bug"):
    """ Context manager to provide monitoring & error handling for some action.

    Before/after some action is performing, logger stored the request, and
    catches all exceptions. If none is caught, the logger stores that the call
    was successful. If one is caught, a pyface dialog is displayed with the
    error message. In the meanwhile, the logger stores the traceback of the
    error in addition to the error message displayed to the user.

    Parameters
    ----------
    action_name : str
        Name of the action to monitor.

    log_folder : str
        Path to the log folder.

    logger : logging.logger.Logger [OPTIONAL]
        Instance of the logger to use for monitoring. If not provided, will use
        the local logger.

    allow_gui : bool
        Whether to allow for a message dialog to be displayed to the user in
        case of an Exception.

    gui_title : str [OPTIONAL]
        Title of the dialog to be displayed if any. Ignored if allow_gui=False.

    gui_severity : str [OPTIONAL]
        Severity of the dialog to be displayed if any. Allowed values are
        'information', 'warning', and 'error'. Ignored if allow_gui=False.

    feedback_menu_name : str
        Menu path/URL to instructions on how to submit bug reports.
    """
    if logger is None:
        logger = local_logger

    logger.debug("Action '{}' requested...".format(action_name))
    try:
        yield
    except Exception as e:
        msg = "Action '{}' failed! \n\nError was:\n{}. \n\n" \
              "Refer to the log file {} for more details or request " \
              "support, following instructions in {}."
        log_file = get_log_file(log_folder)
        msg = msg.format(action_name, e, log_file, feedback_menu_name)
        logger.exception(msg + format_tb())
        if allow_gui:
            from app_common.pyface.monitored_actions import message_dialog

            if gui_severity not in KNOWN_SEVERITIES:
                msg = "Wrong severity {}. Supported values are {}"
                local_logger.error(msg.format(gui_severity, KNOWN_SEVERITIES))
                return

            message_dialog(None, msg, title=gui_title, severity=gui_severity)
    else:
        msg = "Action '{}' performed successfully.".format(action_name)
        logger.debug(msg)


def add_stream_handler_to_root_logger():
    """ Add a development handler to root logger for quick setup.
    """
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    return root_logger
