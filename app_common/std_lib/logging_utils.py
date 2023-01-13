""" Utilities to quickly and consistently add logging infrastruture for
applications.
"""
import time
from logging import DEBUG, FileHandler, Formatter, getLogger, StreamHandler, \
    WARNING
import os
from os.path import isdir, join

from app_common.std_lib.remote_logging_handler import RequestsHTTPHandler

# More than info, less than warning, level to record what actions are used in
# applications: menu entries, navigation buttons, ...
ACTION_LEVEL = 25


def initialize_logging(include_console=True, logging_level=WARNING,
                       log_file=None, log_dir=".", prefix=None, dt_fmt="",
                       include_http=False, http_logger_kw=None):
    """ Set up logging with a console handler and optionally a file handler.

    Parameters
    ----------
    include_console : bool
        Whether to include a console logging handler.

    logging_level : str or int, optional
        Level of sensitivity of the **console handler**. Valid values are
        'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL' or an integer value.
        Ignored if `include_console` is set to `False`.

    log_file : str or None, optional
        The name of the log file. If this is None, the name will be set from
        the prefix and time.

    log_dir : str, optional
        Absolute path to the desired folder to store the log file if any. By
        default, it is stored in the active directory at the function call
        time. Ignored if log_file is provided.

    prefix : None or str, optional
        Prefix for the log file name. Ignored if log_file is provided.

    include_http : bool
        Whether to include an HTTP logging handler.

    http_logger_kw : dict
        http logging keyword arguments, passed to `http_logging_handler` as
        kwargs.

    Returns
    -------
    str
        Path to the log file written to, if any.
    """
    if not dt_fmt:
        dt_fmt = '%Y-%m-%d %H:%M:%S'

    # Initial clean up if needed (useful for multiple runs in ipython)
    root_logger = getLogger()
    if root_logger.handlers:
        root_logger.handlers = []

    fmt = '%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)s] %(message)s'
    formatter = Formatter(fmt, dt_fmt)

    root_logger.setLevel(DEBUG)

    # Set up console handler
    if include_console:
        sh = StreamHandler()
        sh.setLevel(logging_level)
        sh.setFormatter(formatter)
        root_logger.addHandler(sh)

    # If no file provided, create one from prefix, log_dir and current time:
    start_dt = time.strftime("%Y-%m-%d-%H-%M-%S")
    if log_file is None and prefix is not None:
        log_file = prefix + "_{}.log".format(start_dt)

        if not isdir(log_dir):
            os.makedirs(log_dir)

        log_file = join(log_dir, log_file)

    if log_file:
        log_fh = FileHandler(log_file, encoding="utf-8")
        log_fh.setLevel(DEBUG)
        log_fh.setFormatter(formatter)
        root_logger.addHandler(log_fh)
        print("Logging set up. For details on current run, refer to this log "
              "file : {!r}".format(log_file))

    if include_http:
        try:
            http_logging_handler(session_start=start_dt, dt_fmt=dt_fmt,
                                 **http_logger_kw)
        except Exception as e:
            msg = "Failed to create the remote handler. Error was {}".format(e)
            root_logger.error(msg)

    return log_file


def http_logging_handler(url="", logging_level=WARNING,
                         handler_klass=RequestsHTTPHandler, **kwargs):
    """ Create and add HTTP handler to send logging calls to remote API.

    Parameters
    ----------
    url : str
        Address of the host including the http prefix, the address of the host,
        optionally the port and the path to the REST end point to send the POST
        request to.

    kwargs : dict
        Attributes to create the handler. In particular, if using the
        RequestsHTTPHandler, it can to specify an app_name, a username and a
        session_start string to be combined and used as part of the identifier
        of a single application run. It should also include any additional data
        that the API end point needs or that should be stored.

    handler_klass : type, optional
        Handler class to create and add to the root logger. By default, a
        `RequestsHTTPHandler` is created.

    logging_level : int, optional
        Level above which to send log call to HTTP handler.
    """
    http_handler = handler_klass(url, **kwargs)
    http_handler.setLevel(logging_level)

    root_logger = getLogger()
    root_logger.addHandler(http_handler)

    try:
        logger = getLogger(__name__)
        logger.log(logging_level + 10, "Testing new remote handler...")
    except Exception as e:
        root_logger.handlers.remove(http_handler)
        msg = f"Failed to issue a log call, probably because of the remote " \
            f"handler. Removed the remote handler. Error was '{e}'."
        root_logger.error(msg)
    else:
        msg = "Remote handler seems to be working normally."
        logger.debug(msg)

    return http_handler


def add_stream_handler(logging_level=DEBUG):
    """ Add a development handler to root logger for quick setup.
    """
    root_logger = getLogger()
    handler = StreamHandler()
    handler.setLevel(logging_level)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging_level)
    return root_logger
