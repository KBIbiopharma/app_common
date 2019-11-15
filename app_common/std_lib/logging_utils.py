from __future__ import print_function

import time
import logging
import os
from os.path import isdir, join
from six import string_types


def initialize_logging(logging_level="WARNING", log_file=None, log_dir=".",
                       prefix=None, include_console=True):
    """ Set up logging with a console handler and optionally a file handler.

    Parameters
    ----------
    logging_level : str or int, optional
        Level of sensitivity of the console handler. Valid values are 'NOTSET',
        'DEBUG', 'WARNING', 'ERROR', 'CRITICAL'.

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

    Returns
    -------
    str
        Path to the log file written to, if any.
    """
    # Initial clean up if needed (useful for multiple runs in ipython)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers = []

    fmt = '%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)s] %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(fmt, datefmt)

    root_logger.setLevel(logging.DEBUG)

    if include_console:
        sh = logging.StreamHandler()
        if isinstance(logging_level, string_types):
            try:
                sh.setLevel(getattr(logging, logging_level))
            except AttributeError:
                msg = "Invalid logging_level value: {}".format(logging_level)
                raise ValueError(msg)
        else:
            sh.setLevel(logging_level)

        sh.setFormatter(formatter)
        root_logger.addHandler(sh)

    # If no file provided, create one from prefix, log_dir and datetime:
    if log_file is None and prefix is not None:
        log_file_template = prefix + "_%Y-%m-%d-%H-%M-%S.log"
        log_file = time.strftime(log_file_template)

        if not isdir(log_dir):
            os.makedirs(log_dir)

        log_file = join(log_dir, log_file)

    if log_file:
        log_fh = logging.FileHandler(log_file, encoding="utf-8")
        log_fh.setLevel(logging.DEBUG)
        log_fh.setFormatter(formatter)
        root_logger.addHandler(log_fh)
        print("Logging setup. For details on current run, refer to this log "
              "file : {!r}".format(log_file))

    return log_file
