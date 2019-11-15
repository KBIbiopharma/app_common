""" Tests for the AsyncJobManager class.
"""

import time
from unittest import TestCase

from app_common.encore.async_job_manager import AsyncJobManager


def _simple_func(sleep_time):
    time.sleep(max(1, sleep_time % 3) * 0.1)
    return {'sleep_time': sleep_time}


def _simple_job(num_work_items):
    """ Generator to create num_work_items work items.
    """
    for i in range(num_work_items):
        yield _simple_func, (i,), {}


class TestAsyncJobManager(TestCase):

    def setUp(self):
        self.job_mgr = AsyncJobManager()
        self.job_mgr.start()

    def tearDown(self):
        self.job_mgr.shutdown()

    # Tests -------------------------------------------------------------------

    def test_async_job_submission(self):
        num_workitem_1 = 5
        num_workitem_2 = 2
        job_id1 = self.job_mgr.submit(_simple_job, num_workitem_1)
        job_id2 = self.job_mgr.submit(_simple_job, num_workitem_2)

        # when the job is still pending, querying for result
        # should return `None`
        result_1 = self.job_mgr.get_results(job_id1)
        result_2 = self.job_mgr.get_results(job_id2)
        self.assertIsNone(result_1)
        self.assertIsNone(result_2)

        # wait for the jobs to be completed
        self.job_mgr.wait()

        # All the results should now be available
        result_1 = self.job_mgr.get_results(job_id1)
        result_2 = self.job_mgr.get_results(job_id2)
        self.assert_valid_job_result(result_1, num_workitem_1)
        self.assert_valid_job_result(result_2, num_workitem_2)

        # querying multiple times should throw an error
        with self.assertRaises(ValueError):
            self.job_mgr.get_results(job_id1)
        with self.assertRaises(ValueError):
            self.job_mgr.get_results(job_id2)

    # Custom assertions -------------------------------------------------------

    def assert_valid_job_result(self, result, num_workitems):
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), num_workitems)
        for _, val in result.items():
            self.assertEqual(list(val.keys()), ['sleep_time'])

        self.assertEqual(set(val['sleep_time'] for val in result.values()),
                         set(range(num_workitems)))
