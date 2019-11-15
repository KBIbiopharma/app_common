from unittest import TestCase
import logging
import os
from nose.plugins.logcapture import MyMemoryHandler

from app_common.std_lib.logging_utils import initialize_logging


class TestLoggingInitialization(TestCase):
    def setUp(self):
        self.root_logger = logging.getLogger()
        self.init_handlers = [h for h in self.root_logger.handlers]
        self.init_level = self.root_logger.level

    def tearDown(self):
        self.root_logger.handlers = self.init_handlers
        self.root_logger.setLevel(self.init_level)

    def assert_initial_state(self):
        root_logger = self.root_logger
        # By default, if tests run with nose, there is a nose handler:
        if root_logger.handlers:
            self.assertEqual(len(root_logger.handlers), 1)
            self.assertIsInstance(root_logger.handlers[0], MyMemoryHandler)
        else:
            self.assertEqual(len(root_logger.handlers), 0)

    def test_default_initialize_logging(self):
        root_logger = self.root_logger
        self.assert_initial_state()
        initialize_logging()
        self.assertEqual(len(root_logger.handlers), 1)
        self.assertIsInstance(root_logger.handlers[0], logging.StreamHandler)
        self.assertEqual(root_logger.handlers[0].level, logging.WARNING)

    def test_initialize_logging_str_level(self):
        root_logger = self.root_logger
        initialize_logging(logging_level="WARNING")
        self.assertEqual(len(root_logger.handlers), 1)
        self.assertIsInstance(root_logger.handlers[0], logging.StreamHandler)
        self.assertEqual(root_logger.handlers[0].level, logging.WARNING)

        initialize_logging(logging_level="INFO")
        self.assertEqual(len(root_logger.handlers), 1)
        self.assertIsInstance(root_logger.handlers[0], logging.StreamHandler)
        self.assertEqual(root_logger.handlers[0].level, logging.INFO)

    def test_initialize_logging_bad_str_level(self):
        with self.assertRaises(ValueError):
            initialize_logging(logging_level="BLAH")

    def test_initialize_logging_int_level(self):
        root_logger = self.root_logger
        self.assert_initial_state()
        initialize_logging(logging_level=30)
        self.assertEqual(len(root_logger.handlers), 1)
        self.assertIsInstance(root_logger.handlers[0], logging.StreamHandler)
        self.assertEqual(root_logger.handlers[0].level, 30)

    def test_initialize_logging_no_console(self):
        root_logger = self.root_logger
        initialize_logging(include_console=False)
        self.assertEqual(len(root_logger.handlers), 0)

    def test_initialize_with_filelogging(self):
        root_logger = self.root_logger
        self.assert_initial_state()
        filename = "test.log"
        initialize_logging(log_file=filename)
        try:
            self.assertEqual(len(root_logger.handlers), 2)
            self.assertIsInstance(root_logger.handlers[0],
                                  logging.StreamHandler)
            self.assertEqual(root_logger.handlers[0].level, logging.WARNING)

            self.assertIsInstance(root_logger.handlers[1], logging.FileHandler)
            self.assertEqual(root_logger.handlers[1].level, logging.DEBUG)
        finally:
            os.remove(filename)
