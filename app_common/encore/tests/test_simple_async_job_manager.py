from unittest import TestCase
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import cpu_count

from traits.testing.unittest_tools import UnittestTools

from app_common.encore.simple_async_job_manager import \
    RAN_FAILED_STATUS, RESULT_KEY, RESULT_SUCCESSFUL_ITEM, \
    SimpleAsyncJobManager

TWO_WORK_ITEM_JOB_MAX_DURATION = 5
FOUR_WORK_ITEM_JOB_MAX_DURATION = 10

COMPLETED_ATTR_NAME = "work_item_completed"


def custom_sleep(sleep_time, speedup_factor=1.):
    sleep_time /= speedup_factor
    time.sleep(sleep_time)
    return {'sleep_time': sleep_time}


def _simple_job(num_work_items, speedup_factor=1.):
    """ Generator example to create num_work_items work items.
    """
    for i in range(1, num_work_items+1):
        yield custom_sleep, (i,), {"speedup_factor": speedup_factor}


def _broken_func():
    time.sleep(.5)
    raise ValueError("EXPECTED EXCEPTION, PLEASE IGNORE")


def _broken_job():
    """ Generator example to create num_work_items work items.
    """
    yield _broken_func, (), {}


class BaseSimpleJobManager(UnittestTools):

    def setUp(self):
        self.job_mgr = SimpleAsyncJobManager(wait_sleep_period=.3,
                                             **self.attrs)
        self.job_mgrs = [self.job_mgr]

        # Default job length
        self.num_work_items = 2

    def tearDown(self):
        for job_mgr in self.job_mgrs:
            job_mgr.shutdown()

    def test_executor_pool_size(self):
        """ Make sure that JobManager can't have a pool of 0 workers.
        """
        self.assertGreaterEqual(self.job_mgr.max_workers, 1)
        self.assertGreaterEqual(self.job_mgr._executor._max_workers, 1)

        # Cannot create a job manager with a 0-length pool size:
        jm_0_workers = SimpleAsyncJobManager(max_workers=0, **self.attrs)
        self.job_mgrs.append(jm_0_workers)
        num_cpu = cpu_count()
        self.assertEqual(jm_0_workers.max_workers, num_cpu)
        self.assertEqual(jm_0_workers._executor._max_workers, num_cpu)

    def test_submit_run_1_job_n_workitems_async_map_interface(self):
        """ Create job and submit a n-work item job to it using the async_map
        method.
        """
        for num_work_items in range(1, 4):
            with self.assertTraitChangesAsync(
                    self.job_mgr, COMPLETED_ATTR_NAME, count=num_work_items,
                    timeout=FOUR_WORK_ITEM_JOB_MAX_DURATION):
                sleep_times = range(1, num_work_items+1)
                job_id, work_ids = self.job_mgr.async_map(custom_sleep,
                                                          sleep_times)
                self.assertIsInstance(job_id, str)
                self.assertIsInstance(work_ids, list)
                self.assertEqual(len(work_ids), num_work_items)
                # Before it has run test initial state:
                self.assert_job_not_run(self.job_mgr, job_id, work_ids)

            self.assert_job_run(self.job_mgr, job_id, work_ids)

    def test_submit_run_1_job_n_workitems_map_interface(self):
        """ Create job and submit a n-work item job to it using the map
        method.
        """
        for num_work_items in range(1, 4):
            with self.assertTraitChangesAsync(
                    self.job_mgr, COMPLETED_ATTR_NAME, count=num_work_items,
                    timeout=FOUR_WORK_ITEM_JOB_MAX_DURATION):
                sleep_times = range(1, num_work_items+1)
                job_id, work_ids = self.job_mgr.map(custom_sleep, sleep_times)

            self.assertIsInstance(job_id, str)
            self.assertIsInstance(work_ids, list)
            self.assert_job_run(self.job_mgr, job_id, work_ids)

    def test_submit_run_1_job_n_workitems_submit_interface(self):
        """ Create job and submit a n-work item job to it using the lower level
        submit method.
        """
        for num_work_items in range(1, 4):
            with self.assertTraitChangesAsync(
                    self.job_mgr, COMPLETED_ATTR_NAME, count=num_work_items,
                    timeout=FOUR_WORK_ITEM_JOB_MAX_DURATION):
                job_id, work_ids = self.job_mgr.submit(_simple_job,
                                                       num_work_items)
                self.assertIsInstance(job_id, str)
                self.assertIsInstance(work_ids, list)
                self.assertEqual(len(work_ids), num_work_items)
                # Before it has run test initial state:
                self.assert_job_not_run(self.job_mgr, job_id, work_ids)

            self.assert_job_run(self.job_mgr, job_id, work_ids)

    def test_submit_run_2_job_serial(self):
        """ Manager where max_workers is set to 1 can only run 1 job at a time.
        """
        job_mgr = SimpleAsyncJobManager(max_workers=1, **self.attrs)
        self.job_mgrs.append(job_mgr)
        num_work_items = self.num_work_items
        with self.assertTraitChangesAsync(
                job_mgr, COMPLETED_ATTR_NAME, count=2*num_work_items,
                timeout=2*TWO_WORK_ITEM_JOB_MAX_DURATION):
            with self.assertTraitChangesAsync(
                    job_mgr, COMPLETED_ATTR_NAME, count=num_work_items,
                    timeout=TWO_WORK_ITEM_JOB_MAX_DURATION):
                job_id1, wk_ids = job_mgr.submit(_simple_job, num_work_items)
                self.assert_job_not_run(job_mgr, job_id1, wk_ids)
                job_id2, wk_ids2 = job_mgr.submit(_simple_job, num_work_items)
                self.assert_job_not_run(job_mgr, job_id2, wk_ids2)

            # In half the time, the first job is finished and the second isn't
            self.assert_job_run(job_mgr, job_id1, wk_ids)
            self.assert_job_not_run(job_mgr, job_id2, wk_ids2)

        self.assert_job_run(job_mgr, job_id2, wk_ids2)
        # Once all jobs have run, there is not pending jobs
        self.assertEqual(len(job_mgr._pending_jobs), 0)

    def test_submit_run_2_job_parallel(self):
        num_run = 2
        self.assert_job_manager_runs_in_parallel(num_run)

    def test_submit_run_4_job_parallel(self):
        num_run = 4
        self.assert_job_manager_runs_in_parallel(num_run)

    def test_wait(self):
        job_id, work_ids = self.job_mgr.submit(_simple_job,
                                               self.num_work_items)
        job_id2, work_ids2 = self.job_mgr.submit(_simple_job,
                                                 self.num_work_items)
        self.assert_job_not_run(self.job_mgr, job_id, work_ids)
        self.assert_job_not_run(self.job_mgr, job_id2, work_ids2)
        self.job_mgr.wait()
        self.assert_job_run(self.job_mgr, job_id, work_ids)
        self.assert_job_run(self.job_mgr, job_id2, work_ids2)

    def test_wait_for_specific_job(self):
        # Make things serial so that second job can't start before first has
        # ended
        job_mgr = SimpleAsyncJobManager(max_workers=1, **self.attrs)
        self.job_mgrs.append(job_mgr)

        job_id, work_ids = job_mgr.submit(_simple_job, self.num_work_items)
        job_id2, work_ids2 = job_mgr.submit(_simple_job, self.num_work_items)
        self.assert_job_not_run(job_mgr, job_id, work_ids)
        self.assert_job_not_run(job_mgr, job_id2, work_ids2)
        job_mgr.wait(job_id=job_id)
        self.assert_job_run(job_mgr, job_id, work_ids)
        self.assert_job_not_run(job_mgr, job_id2, work_ids2)

    def test_wait_for_specific_work_item(self):
        # Make things serial so that second job can't start before first has
        # ended
        job_mgr = SimpleAsyncJobManager(max_workers=1, wait_sleep_period=.1,
                                        **self.attrs)
        self.job_mgrs.append(job_mgr)

        num_work_items = 4
        job_id, work_ids = job_mgr.submit(_simple_job, num_work_items,
                                          speedup_factor=2)
        for i in range(num_work_items):
            job_mgr.wait(job_id=job_id, work_id=work_ids[i])
            self.assertEqual(len(job_mgr._pending_jobs), num_work_items-(i+1))

    def test_get_results(self):
        job_id, work_ids = self.job_mgr.submit(_simple_job,
                                               self.num_work_items)
        results = self.job_mgr.get_results(job_id)
        self.assertIsNone(results)
        self.job_mgr.wait()
        results = self.job_mgr.get_results(job_id)
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), self.num_work_items)
        for work_id, result in results.items():
            self.assertIsInstance(work_id, str)
            self.assertIsInstance(result, dict)
        # Can only request a result once since it is removed from the JM after
        with self.assertRaises(ValueError):
            self.job_mgr.get_results(job_id)

        # Once all jobs have run, there is not pending jobs
        self.assertEqual(len(self.job_mgr._pending_jobs), 0)

    def test_get_results_one_item_at_a_time(self):
        job_id, work_ids = self.job_mgr.submit(_simple_job,
                                               self.num_work_items)
        self.job_mgr.wait()
        for i, work_id in enumerate(work_ids):
            results = self.job_mgr.get_results(job_id, work_id=work_id)
            expected = {'sleep_time': i+1.,
                        RESULT_KEY: RESULT_SUCCESSFUL_ITEM}
            self.assertEqual(results, expected)

        # Can only request a result once since it is removed from the JM after
        for work_id in work_ids:
            with self.assertRaises(ValueError):
                self.job_mgr.get_results(job_id, work_id)

        # Once all jobs have run, there is not pending jobs
        self.assertEqual(len(self.job_mgr._pending_jobs), 0)

    def test_get_results_many_work_items_high_speed(self):
        num_work_items = 100
        job_id, work_ids = self.job_mgr.submit(
            _simple_job, num_work_items, speedup_factor=1000.
        )
        self.job_mgr.wait()
        results = self.job_mgr.get_results(job_id)
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), num_work_items)
        for work_id, result in results.items():
            self.assertIsInstance(work_id, str)
            self.assertIsInstance(result, dict)
        # Can only request a result once since it is removed from the JM after
        with self.assertRaises(ValueError):
            self.job_mgr.get_results(job_id)

    def test_zero_second_jobs(self):
        def _simple_job_with_zero(num_work_items):
            # This version of the job generator creates 0 second jobs:
            for i in range(0, num_work_items):
                yield custom_sleep, (i,), {}

        job_id, work_ids = self.job_mgr.submit(_simple_job_with_zero, 3)
        self.job_mgr.wait()
        results = self.job_mgr.get_results(job_id)
        self.assertIsInstance(results, dict)

    def test_get_results_many_jobs(self):
        # We will make 1000 jobs with 1 item each:
        num_jobs = 1000
        job_ids = []
        for _ in range(num_jobs):
            job_id, work_ids = self.job_mgr.submit(
                _simple_job, 1, speedup_factor=100
            )
            job_ids.append(job_id)

        self.job_mgr.wait()

        for job_id in job_ids:
            results = self.job_mgr.get_results(job_id)
            self.assertIsInstance(results, dict)
            self.assertEqual(len(results), 1)

        # Once all jobs have run, there is not pending jobs
        self.assertEqual(len(self.job_mgr._pending_jobs), 0)

    def test_fail_job(self):
        job_id, work_ids = self.job_mgr.submit(_broken_job)
        work_id = work_ids[0]
        id_tuple = (job_id, work_id)
        self.assertIsNone(self.job_mgr.get_results(job_id))
        future = self.job_mgr._futures_id_map[id_tuple]
        with self.assertRaises(ValueError):
            future.result()

        status = self.job_mgr.get_status(job_id, work_id=work_id)
        self.assertEqual(status, RAN_FAILED_STATUS)
        results = self.job_mgr.get_results(job_id, work_id)
        exception_result = "ITEM FAILED WITH EXCEPTION:"
        self.assertTrue(results[RESULT_KEY].startswith(exception_result))
        # Once all jobs have run, there is not pending jobs
        self.assertEqual(len(self.job_mgr._pending_jobs), 0)

    # Helper methods ----------------------------------------------------------

    def assert_job_manager_runs_in_parallel(self, num_parallel):
        if cpu_count() < num_parallel:
            self.skipTest("Not enough CPUs to run this test.")

        job_mgr = SimpleAsyncJobManager(max_workers=num_parallel, **self.attrs)
        self.job_mgrs.append(job_mgr)
        num_work_item = 2
        # 2 jobs, with 2 work items in each, means 1s for the first work item,
        # and 2s for the second work item, meaning 3s for each job. In serial,
        # that's num_parallel*3 seconds plus overhead. Test that his happens in
        # strictly less amount of time:
        eps = 0.3
        jobs = []
        works = []
        with self.assertTraitChangesAsync(
                job_mgr, COMPLETED_ATTR_NAME, count=num_parallel*num_work_item,
                timeout=num_parallel*3-eps):
            for i in range(num_parallel):
                job_id, wk_ids = job_mgr.submit(_simple_job, num_work_item)
                self.assert_job_not_run(job_mgr, job_id, wk_ids)
                jobs.append(job_id)
                works.append(wk_ids)

        # Once the results are triggered enough times, all jobs are finished
        for job_id, wk_ids in zip(jobs, works):
            self.assert_job_run(job_mgr, job_id, wk_ids)

    def assert_job_not_run(self, job_mgr, job_id, work_ids):
        pending_jobs = job_mgr._pending_items_for_job(job_id)
        results = job_mgr._job_results
        self.assertEqual(pending_jobs, set(work_ids))
        self.assertEqual(results[job_id], {})

    def assert_job_run(self, job_mgr, job_id, work_ids):
        pending_jobs = job_mgr._pending_items_for_job(job_id)
        results = job_mgr._job_results

        self.assertEqual(pending_jobs, set())
        self.assertIn(job_id, results)
        self.assertEqual(set(results[job_id].keys()), set(work_ids))
        for work_id, result in results[job_id].items():
            self.assertIsInstance(work_id, str)
            self.assertIsInstance(result, dict)
            self.assertEqual(list(result.keys()), ['sleep_time', RESULT_KEY])
            self.assertEqual(result[RESULT_KEY], RESULT_SUCCESSFUL_ITEM)


class TestSimpleMultiProcJobManager(BaseSimpleJobManager, TestCase):
    """ Test JobManager using a ProcessPool to execute jobs.
    """
    @classmethod
    def setUpClass(cls):
        # No additional traits set, so default executor used (ProcessPool)
        cls.attrs = {"_executor_klass": "ProcessPoolExecutor"}

    def test_default_attrs(self):
        self.assertIsInstance(self.job_mgr._executor, ProcessPoolExecutor)


class TestSimpleMultiThreadJobManager(BaseSimpleJobManager, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.attrs = {"_executor_klass": "ThreadPoolExecutor"}

    def test_default_attrs(self):
        self.assertIsInstance(self.job_mgr._executor, ThreadPoolExecutor)
