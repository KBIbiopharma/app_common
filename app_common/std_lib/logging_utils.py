"""
"""
import time
from logging import DEBUG, FileHandler, Formatter, getLogger, Handler, INFO, \
    StreamHandler, WARNING
from datetime import datetime
import os
from os.path import isdir, join
import requests
from uuid import uuid4

from app_common.std_lib.os_utils import collect_user_name


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
                         **kwargs):
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
    if pkg_list is None:
        pkg_list = ["app_common"]

    if not dt_fmt:
        dt_fmt = "%Y/%m/%d %H:%M:%S"

    http_handler = CustomHTTPHandler(url, dt_fmt=dt_fmt, **kwargs)
    http_handler.setLevel(logging_level)

    # Only remote log the application's messages to avoid noise and
    # RecursionError because requests sends logging messages:
    for pkg in pkg_list:
        logger = getLogger(pkg)
        logger.addHandler(http_handler)

        try:
            logger.log(logging_level+10, "Testing new remote handler...")
        except Exception as e:
            logger.handlers.remove(http_handler)
            msg = "Failed to issue a log call, probably because of the " \
                  "remote handler. Removed the remote handler. Error was '{}'."
            msg = msg.format(e)
            logger.error(msg)
        finally:
            break

    return http_handler


class CustomHTTPHandler(Handler):
    """ Custom HTTPHandler passing the HTTP request using the requests.post
    method, since it tends to be more stable for REST API end points.
    """
    def __init__(self, url, app_name="", start_dt="", dt_fmt="", **adtl_data):
        """ Initialize the instance with the request URL and all parameters.
        """
        super(CustomHTTPHandler, self).__init__()
        self.url = url
        self.app_name = app_name
        self.adtl_data = adtl_data
        self.start_dt = start_dt
        self.dt_fmt = dt_fmt

    def emit(self, record):
        """ Custom implementation of emit using requests.post since it tends to
        work more easily with REST API end points.
        """
        data = self.map_log_record(record)
        # Build a valid json string with the data to record:
        data_str = str(data).replace("'", '"')
        response = requests.post(self.url, data=data_str)
        return response

    def map_log_record(self, record):
        """ Custom implementation of mapping the log record into a dict.
        """
        # Generate utc datetime since default logging collects local time:
        utc_datetime = datetime.strftime(datetime.utcnow(), self.dt_fmt)
        username = collect_user_name()
        # This log_id should be unique and constant throughout a tool
        # usage:
        session_id = self.app_name + ":" + username + ":" + self.start_dt
        data = {
            "log_id": str(uuid4()),
            "session_id": session_id,
            "app_name": self.app_name,
            'user': username,
            "pkg": record.name,
            'level_no': record.levelno,
            'line_no': record.lineno,
            'func_name': record.funcName,
            'utc_timestamp': utc_datetime,
            'msg': record.msg
        }
        data.update(self.adtl_data)

        return data


def add_stream_handler(logging_level=DEBUG):
    """ Add a development handler to root logger for quick setup.
    """
    root_logger = getLogger()
    handler = StreamHandler()
    handler.setLevel(logging_level)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging_level)
    return root_logger
