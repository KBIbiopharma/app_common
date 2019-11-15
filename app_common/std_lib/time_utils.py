from __future__ import print_function

import types
import logging
from contextlib import contextmanager
from time import time

logger = logging.getLogger(__name__)

UNIT_FACTORS = {"sec": 1.,
                "min": 60.,
                "hr": 3600.}


@contextmanager
def timeit(fmt_precision=2, units="sec", action_name="execution",
           reporter=print):
    """ Execute a task and display the duration time the task took.

    Parameters
    ----------
    fmt_precision : int, Optional
        Number of digits to use to display the number of seconds.

    units : str, Optional
        Name of the unit of the result.

    action_name : str, Optional
        Name of the action being timed, to customize the message.

    reporter : callable, Optional
        Callable to report the execution time. Defaults to the print function,
        but a logger method or other callables can be passed.
    """
    start = time()
    yield
    duration = time()-start
    duration /= UNIT_FACTORS[units]
    msg = "{} time: {:.%sf} {}." % fmt_precision
    reporter(msg.format(action_name.capitalize(), duration, units))


def timed_call(report="print"):
    """ Decorator generator to time and report the execution of a function.

    Parameters
    ----------
    report : str or callable [OPTIONAL]
        Description of how to report the execution time. Supported values are
        'log' and 'print', or a callable.

    Examples
    --------
    >>> @timed_call()
        def sleeping_func():
            time.sleep(.2)
    >>> sleeping_func()
    Execution time for sleeping_func was 0.203s
    """
    def timed_operation(func):
        def timed_func(*args, **kwargs):
            start = time()
            out = func(*args, **kwargs)
            duration = time() - start
            msg = "Execution time for {} was {:.3f}s"
            msg = msg.format(func.__name__, duration)
            if report == "log":
                logger.debug(msg)
            elif report == "print":
                print(msg)
            elif isinstance(report, (types.FunctionType, types.MethodType)):
                report(msg)
            else:
                msg = "Unknown report value: {} (type {}). Supported values " \
                      "are 'log' and 'print' or a custom callable."
                logger.error(msg.format(report, type(report)))
            return out

        return timed_func
    return timed_operation
