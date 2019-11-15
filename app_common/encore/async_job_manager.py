""" Definition of AsyncJobManager to schedule and execute jobs asynchronously.
"""
import logging
import threading

from traits.api import Any, Dict, Instance, Int, List
from encore.concurrent.futures.abc_work_scheduler import (
    ABCWorkScheduler
)
from encore.concurrent.futures.enhanced_thread_pool_executor import (
    EnhancedThreadPoolExecutor
)
from encore.concurrent.futures.serializer import Serializer

from ..std_lib.sys_utils import print_traceback
from .job_manager import JobManager

logger = logging.getLogger(__name__)


class AsyncJobManager(JobManager):
    """ A Manager that supports async execution using Thread pools.
    """
    #: Implementation of a Job which must receive a work_factory callable
    #: argument, and its arguments, and has a iter_work_items method that
    #: yields work items. Both the job and the work item are expected to have
    #: an `id` attribute.
    job_class = Any

    #: Max number of thread workers. If 0, multiprocessing.cpu_count used.
    max_workers = Int(1)

    #: The executor used for supporting asynchronized operation.
    _executor = Instance(EnhancedThreadPoolExecutor)

    #: The scheduler for managing the jobs.
    _scheduler = Instance(ABCWorkScheduler)

    #: Dictionary containing the results from the finished jobs, until queried.
    #: NOTE: This dictionary is also updated by worker threads so take a lock,
    #: before accessing the dict.
    _job_results = Dict

    #: Lock to update the results safely.
    _state_lock = threading.Condition()

    #: The list of submitted jobs that are pending or currently executing.
    _pending_jobs = List

    def get_results(self, job_id):
        """ Collect the results from Job with id job_id.

        FIXME: support checking and returning asap
        """
        with self._state_lock:
            job_results = self._job_results
            if job_id in job_results:
                return job_results.pop(job_id)
            elif job_id in self._pending_jobs:
                return None
            else:
                msg = 'The job {} is not currently scheduled.'.format(job_id)
                logger.exception(msg)
                raise ValueError(msg)

    def start(self):
        if self._scheduler is not None:
            msg = 'The job manager is already active'
            logger.exception(msg)
            raise ValueError(msg)

        self._executor = EnhancedThreadPoolExecutor(
            max_workers=self.max_workers,
            name='job threadpool executor'
        )
        # FIXME: It might be nice to support priority queue for the jobs
        # for now, just using a Serializer that cycles through the job in the
        # order they were submitted.
        self._scheduler = Serializer(
            executor=self._executor,
            callback=self._job_completed,
            name='job scheduler'
        )

    def shutdown(self):
        """ Shuts down manager, releasing resources.

        FIXME: add support for emptying the task list if user wants to.
        """
        logger.info("Shutting down the job manager {}.".format(self.name))
        self._scheduler.shutdown()
        self._executor.shutdown()
        self._scheduler = None
        self._executor = None

    def submit(self, work_factory, *args, **kwargs):
        """ Build Job around the sims submitted to run and submit to scheduler.
        """
        job = self.job_class(work_factory=work_factory,
                             work_factory_args=(args, kwargs))

        with self._state_lock:
            self._pending_jobs.append(job.id)
        self._scheduler.submit(self._process_job, job)

        return job.id

    def wait(self):
        # FIXME: wait on a specific job_id ?
        # perhaps support an argument `poll` that specifies the
        # num. of seconds to sleep before successive checks for the
        # completion of a job.
        self._scheduler.wait()

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def _process_job(self, job):
        """ Process all work items of a job.

        Parameters
        ----------
        job : Instance(Job)
            The job to be processed.

        Returns
        -------
        results : dict
            The returned dict always has the id of the processed job and the
            status of the processing. If the job failed to execute for any
            reason, then `status` is set to `failed`, else it is set to
            `normal`. On successful job execution, the key `results` contains
            the results for the job.
        """
        try:
            job_results = self._process_job_work_items(job)
        except Exception as e:
            print_traceback()
            return {
                'id': job.id,
                'status': 'failed',
                'exception': e
            }
        else:
            return {
                'id': job.id,
                'status': 'normal',
                'results': job_results
            }

    def _process_job_work_items(self, job):
        # FIXME: use a EnhancedThreadPoolExecutor to run the work items
        # for now, just execute them in a single thread one-by-one
        job_results = {}
        for work_item in job.iter_work_items():
            work_id = work_item.id
            work_func = work_item.work_func
            args, kwargs = work_item.work_func_args
            out = work_func(*args, **kwargs)
            job_results[work_id] = out
        return job_results

    def _job_completed(self, future):
        """ Called when a job is completed.
        """
        # FIXME: more fine-grained error handling
        # This should never raise an exception as `_process_job` is handled
        # appropriately.
        try:
            out = future.result()
        except Exception as e:
            msg = ("Failed to retrieve the results from future {}. Error was "
                   "{}".format(future, e))
            logger.exception(msg)
            raise

        job_id = out['id']
        if out['status'] == 'normal':
            logger.info('Completed job : {}'.format(job_id))
            job_results = out['results']
        else:
            e = out['exception']
            logger.exception(
                'Failed to complete job {} : {}'.format(job_id, e.message)
            )
            job_results = None

        with self._state_lock:
            self._pending_jobs.remove(job_id)
            self._job_results[job_id] = job_results

    def _job_class_default(self):
        from .job import Job
        return Job
