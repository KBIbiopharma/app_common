from unittest import TestCase

import time
from app_common.std_lib.time_utils import timeit, timed_call
from app_common.std_lib.sys_utils import capture_stdout

REPORT_MSG = ""

MSG_PREFIX = "Execution time for sleeping_func was"


class TestTimeIt(TestCase):
    def test_usage(self):
        with timeit():
            time.sleep(.2)

    def test_usage_with_fmt(self):
        with timeit(fmt_precision=3):
            time.sleep(.2)


class TestTimedCall(TestCase):
    def test_default(self):
        """ Default behavior runs. """
        @timed_call()
        def sleeping_func():
            time.sleep(.2)

        sleeping_func()

    def test_print_info(self):
        with capture_stdout(steam_close=False) as str_io:
            @timed_call(report="print")
            def sleeping_func():
                time.sleep(.2)

            sleeping_func()
            self.assertIn(MSG_PREFIX, str_io.getvalue())

    def test_log_info(self):
        @timed_call(report="log")
        def sleeping_func():
            time.sleep(.2)

        sleeping_func()

    def test_custom_callable_info(self):
        """ Custom handling of the message: catch it and put it in global var.
        """
        global REPORT_MSG

        def catch(msg):
            global REPORT_MSG
            REPORT_MSG = msg

        @timed_call(report=catch)
        def sleeping_func():
            time.sleep(.2)

        sleeping_func()
        self.assertIn(MSG_PREFIX, REPORT_MSG)
        REPORT_MSG = ""

    def test_fail(self):
        """ Make sure failure doesn't prevent execution. """
        @timed_call(report="BLAH")
        def sleeping_func():
            time.sleep(.2)

        sleeping_func()
