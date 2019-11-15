""" Set of command line tools to interact with users.
"""
import logging
from six.moves import input
from time import sleep
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def yn_question(prompt=None, default_value='yes'):
    """ Prompts user with a yes/no question, returns whether yes was selected.

    Ignores letter casing, and supports typing nothing, yes, no, or the first
    letter or each. If noting is typed, the default value is used.

    Parameters
    ----------
    prompt : str
        Question to be answered by yes or no.

    default_value : str [OPTIONAL, default='yes']
        Default value if the enter just hit 'Enter'. Should be 'yes' or 'no'.

    Returns
    -------
    bool
        Whether yes was answered.
    """
    if default_value.startswith("y"):
        other_value = "no"
    else:
        other_value = "yes"

    prompt = '{} [{}]|{}:'.format(prompt, default_value[0], other_value[0])

    while True:
        ans = input(prompt).lower()
        if not ans:
            ans = default_value
        elif ans not in ['y', 'n', 'yes', 'no']:
            print("Please enter 'y' or 'n'.")
            continue

        return ans[0] == "y"


@contextmanager
def try_action(action_name="action", retry_delay=1, max_retry=0):
    """ Context manager to try something over and over again until it works.

    Useful for operations that are prone to fail and that we would like to try
    multiple times, such as accessing shared or remote resources.
    """
    success = False
    attempt = 0
    while not success:
        try:
            yield
            success = True
        except Exception as e:
            msg = "Failed to {}. Exception was {}. Retrying in {} seconds..."
            msg = msg.format(action_name, e, retry_delay)
            logger.warn(msg)
            sleep(retry_delay)

        if max_retry:
            attempt += 1
            if attempt > max_retry:
                msg = "Failed to {} {} times. Aborting."
                msg = msg.format(action_name, attempt)
                logger.exception(msg)
                raise ValueError(msg)
