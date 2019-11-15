from unittest import TestCase, skipUnless
import numpy as np
import time
import os

from app_common.encore.simple_async_job_manager import \
    SimpleAsyncJobManager

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if BACKEND_AVAILABLE:
    from app_common.encore.job_manager_pane import JobManagerPane, \
        JM_STATE_IDLE, JM_STATE_RUNNING
    from app_common.apptools.testing_utils import temp_bringup_ui_for


def _simple_func(sleep_time, speedup_factor=1.):
    sleep_time /= speedup_factor
    time.sleep(sleep_time)
    return {'sleep_time': sleep_time}


def _simple_job(num_work_items, speedup_factor=1.):
    """ Generator example to create num_work_items work items.
    """
    for i in range(1, num_work_items+1):
        yield _simple_func, (i,), {"speedup_factor": speedup_factor}


@skipUnless(BACKEND_AVAILABLE, "No backend available to paint into")
class TestJobManagerPane(TestCase):

    def setUp(self):
        self.job_mgr = SimpleAsyncJobManager(max_workers=2)
        self.pane = JobManagerPane(job_manager=self.job_mgr,
                                   run_time_result_key='sleep_time')

    def tearDown(self):
        self.pane.prepare_destroy()
        self.job_mgr.shutdown()

    def test_initial_state(self):
        self.assert_n_jobs_submitted(0)

    def test_bring_up(self):
        with temp_bringup_ui_for(self.pane):
            pass

    def test_submit_job(self):
        self.job_mgr.start()
        num_work_items = 2
        self.job_mgr.submit(_simple_job, num_work_items)
        self.assert_n_jobs_submitted(2)
        self.job_mgr.wait()
        self.assert_n_jobs_finished(2)

    def test_submit_job_compute_eta(self):
        self.job_mgr.start()
        num_work_items = 2
        self.job_mgr.submit(_simple_job, num_work_items)
        self.job_mgr.wait()
        self.assert_n_jobs_finished(2)
        self.job_mgr.submit(_simple_job, num_work_items)
        # Now that other jobs have run before, an ETA can be computed. Short
        # tasks so eta computed in seconds.
        # 1.5 seconds because there were 2 jobs before, with runtimes 1 and 2
        # seconds, and there are now 2 jobs, and 2 workers:
        self.assertEqual(self.pane.eta, "1.5 sec")

    def test_submit_job_clear_results(self):
        self.job_mgr.start()
        num_work_items = 2
        self.job_mgr.submit(_simple_job, num_work_items)
        self.job_mgr.wait()
        self.assert_n_jobs_finished(2)
        self.pane.clear_results_button = True
        # Table cleared...
        self.assertEqual(len(self.pane.job_results), 0)
        # ... but tally of all run jobs unchanged:
        self.assertEqual(self.pane.num_run_work_items, num_work_items)

    # Utilities ---------------------------------------------------------------

    def assert_n_jobs_submitted(self, num_work_items):
        self.assertTrue(np.isnan(self.pane.avg_job_duration))
        self.assertEqual(self.pane.num_pending_jobs, num_work_items)
        self.assertEqual(self.pane.num_run_work_items, 0)
        self.assertEqual(self.pane.eta, "")
        if num_work_items > 0:
            self.assertEqual(self.pane.job_manager_state, JM_STATE_RUNNING)
        self.assertEqual(len(self.pane.job_results), 0)

    def assert_n_jobs_finished(self, num_work_items):
        if num_work_items > 0:
            self.assertFalse(np.isnan(self.pane.avg_job_duration))

        self.assertEqual(self.pane.num_pending_jobs, 0)
        self.assertEqual(self.pane.num_run_work_items, num_work_items)
        self.assertEqual(self.pane.eta, "")
        self.assertEqual(self.pane.job_manager_state, JM_STATE_IDLE)
        self.assertEqual(len(self.pane.job_results), num_work_items)
