""" Utilities to quickly and consistently add logging infrastruture for
applications.
"""
import time
from logging import DEBUG, FileHandler, Formatter, getLogger, Handler, INFO, \
    StreamHandler, WARNING
import os
from os.path import isdir, join



def initialize_logging(logging_level=WARNING, log_file=None, log_dir=".",
                       prefix=None, include_console=True, include_http=False,
                       http_logger_kw=None):
    """ Set up logging with a console handler and optionally a file handler.

    Parameters
    ----------
    logging_level : str or int, optional
        Level of sensitivity of the **console handler**. Valid values are
        'NOTSET', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL' or an integer value.

    log_file : str or None, optional
        The name of the log file. If this is None, the name will be set from
        the prefix and time.

    log_dir : str, optional
        Absolute path to the desired folder to store the log file if any. By
        default, it is stored in the active directory at the function call
        time. Ignored if log_file is provided.

    prefix : None or str, optional
        Prefix for the log file name. Ignored if log_file is provided.

    include_console : bool
        Whether to include a console logging handler.

    include_http : bool
        Whether to include an HTTP logging handler.

    http_logger_kw : dict
        http logging keyword arguments, passed to

    Returns
    -------
    str
        Path to the log file written to, if any.
    """
    # Initial clean up if needed (useful for multiple runs in ipython)
    root_logger = getLogger()
    if root_logger.handlers:
        root_logger.handlers = []

    fmt = '%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)s] %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    formatter = Formatter(fmt, datefmt)

    root_logger.setLevel(DEBUG)

    if include_console:
        sh = StreamHandler()
        sh.setLevel(logging_level)
        sh.setFormatter(formatter)
        root_logger.addHandler(sh)

    # If no file provided, create one from prefix, log_dir and datetime:
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
        print("Logging setup. For details on current run, refer to this log "
              "file : {!r}".format(log_file))

    if include_http:
        try:
            http_logging_handler(start_dt=start_dt, **http_logger_kw)
        except Exception as e:
            msg = "Failed to create the remote handler. Error was {}".format(e)
            root_logger.error(msg)

    return log_file


def http_logging_handler(url="", pkg_list=None, dt_fmt="", logging_level=INFO,
                         handler_klass=CustomHTTPHandler, **kwargs):
    """ Create and add HTTP handler to send logging calls to remote API.

    Parameters
    ----------
    url : str
        Address of the host including the http prefix, the address of the host,
        optionally the port and the path to the REST end point to send the POST
        request to.

    kwargs : dict
        Attributes to the CustomHTTPHandler. In particular, it needs to specify
        an app_name, start_dt to be combined and used as an identifier of a
        single session. Should also include any additional data that the API
        end point needs or that should be stored.

    pkg_list : list
        List of package names to use this handler on. NOTE: this handler cannot
        be used on the root handler, because that creates a RecursionError due
        to the way requests.post is implemented.

    dt_fmt : str, optional
        Custom formatting for the UTC datetime to be passed to the logging
        call.

    logging_level : int, optional
        Level above which to send log call to HTTP handler. Defaults to INFO.
    """
    if not dt_fmt:
        dt_fmt = "%Y/%m/%d %H:%M:%S"

    http_handler = CustomHTTPHandler(url, dt_fmt=dt_fmt, **kwargs)
    http_handler.setLevel(logging_level)

    logger = getLogger()
    logger.addHandler(http_handler)

    try:
        logger.log(logging_level+10, "Testing new remote handler...")
        msg = "Remote handler seems to be working normally."
        logger.debug(msg)
    except Exception as e:
        logger.handlers.remove(http_handler)
        msg = "Failed to issue a log call, probably because of the " \
              "remote handler. Removed the remote handler. Error was '{}'."
        msg = msg.format(e)
        logger.error(msg)

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
