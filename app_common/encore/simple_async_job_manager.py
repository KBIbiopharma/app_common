""" Definition of a simple AsyncJobManager to schedule and execute jobs
asynchronously using a pool of threads or processes.
"""
import logging
import multiprocessing
from time import sleep, time
import threading
from concurrent.futures import Executor

from traits.api import Any, Bool, Dict, Enum, Event, Float, HasStrictTraits, \
    Instance, Int, Set, Str

from .job_manager import JobManager

# All possible status for a work item:
PENDING_STATUS = "Submitted"
RUNNING_STATUS = "Running"
RAN_SUCCESSFULLY_STATUS = "Ran successfully"
RAN_FAILED_STATUS = "Failed to run"
CANCELLED_STATUS = "Cancelled"

ALL_STATUS = [PENDING_STATUS, RUNNING_STATUS, RAN_SUCCESSFULLY_STATUS,
              RAN_FAILED_STATUS, CANCELLED_STATUS]

# Possible result values:
RESULT_SUCCESSFUL_ITEM = "ITEM RAN"
RESULT_CANCELLED_ITEM = "ITEM CANCELLED"
RESULT_EXCEPTION_ITEM = "ITEM FAILED WITH EXCEPTION: '{}'."

RESULT_KEY = "results"

# Name of the attribute to add to the future object, to track which work item
# has finished
FUTURE_ATTR_NAME = "_job_manager_id"

logger = logging.getLogger(__name__)


class TimeOutError(RuntimeError):
    pass


class JobManagerEvent(HasStrictTraits):
    job_id = Str

    work_id = Str


class SimpleAsyncJobManager(JobManager):
    """ A Manager that supports async execution using process or thread pools.

    To use, first call the start method to create

    By default, the job manager uses a process pool, but an _executor instance
    can be passed at creation to use a different
    :class:`concurrent.futures.Executor`. Also the size of the process/thread
    pool can be controlled by setting the :attr:`max_workers` attribute, so as
    to avoid overloading the OS with too many processes/threads.

    Finally, it is important to call the :meth:`shutdown` method after use to
    clean up resources. Creating too many job managers without shutting them
    down will overload the OS.

    TODO:
    - Support a max pending job size?

    Examples
    --------
    >>> def sleeper(sleep_time):
            # Function to execute in parallel. Must return a dict.
            sleep(sleep_time)
            return {"sleep_time": sleep_time}

    >>> jm = SimpleAsyncJobManager()
    # Submit 5 jobs, each sleeping 2 seconds:
    >>> jm.async_map(sleeper, [2]*5)  # non-blocking
    # Optional: wait on all currently submitted jobs before returning
    >>> jm.wait()
    """

    # FIXME:
    # - Occasional segfault 11 on OSX :
    #
    # Crashed Thread:        2
    # Exception Type:        EXC_BAD_ACCESS (SIGSEGV)
    # Exception Codes:       KERN_INVALID_ADDRESS at 0x0000000000000000
    #
    # Thread 2 Crashed:
    # 0   libsystem_platform.dylib      	0x00007fff9ad92fbd _platform_memmove$VARIANT$Haswell + 157  # noqa
    # 1   interpreter.so                	0x000000011aee5828 th_worker(void*) + 456  # noqa

    #: Implementation of a Job which must receive a work_factory callable
    #: argument, and its arguments, and has a iter_work_items method that
    #: yields work items. Both the job and the work item are expected to have
    #: an `id` attribute.
    job_class = Any

    #: Max number of workers. If 0, multiprocessing.cpu_count used.
    max_workers = Int

    #: Updated when work item completed
    work_item_completed = Event(JobManagerEvent)

    #: Amount of time (in sec) between 2 pollings while waiting on pending jobs
    wait_sleep_period = Float(.5)

    #: The executor used for supporting asynchronized operation.
    # Typical objects here would be concurrent.futures's ProcessPoolExecutor or
    # ThreadPoolExecutor
    _executor = Instance(Executor)

    #: Class name to create the _executor if not provided
    _executor_klass = Enum(["ProcessPoolExecutor", "ThreadPoolExecutor"])

    #: Dictionary of futures created.
    # future removed when successfully ran so futures left in it are work items
    # that led to an exception.
    _futures_id_map = Dict

    #: Dictionary containing the results from the finished jobs, until queried.
    # NOTE: This dictionary is also updated by worker threads so protect
    # accessing the dict using the thread _state_lock.
    _job_results = Dict

    #: Set of work items still to run
    # NOTE: This dictionary is also updated by worker threads so protect
    # accessing the dict using the thread _state_lock.
    _pending_jobs = Set

    #: Lock to update the results safely.
    _state_lock = threading.Condition()

    _shutting_down = Bool(False)

    def __init__(self, **traits):
        # Prevent users from making a job manager with a process pool of size
        # 0 because submitting jobs to it will never end.
        if traits.get("max_workers", 1) < 1:
            traits.pop("max_workers")

        super(SimpleAsyncJobManager, self).__init__(**traits)
        msg = "Starting a SimpleAsyncJobManager with {} workers."
        msg = msg.format(self.max_workers)
        logger.debug(msg)

    # Job submission methods --------------------------------------------------

    def map(self, callable, *args, **kwargs):
        """ Submit a job (multiple work items) using the Pool style interface.

        Pass the worker callable and the list of arguments, one argument for
        each work item. (blocking).

        See Also
        --------
        async_map
            Non-blocking version of this method.
        """
        job_id, work_ids = self.async_map(callable, *args, **kwargs)
        self.wait()
        return job_id, work_ids

    def async_map(self, callable, arg_list, **kwargs):
        """ Submit a job (multiple work items) using the Pool style interface.

        Pass the worker callable and the list of arguments, one argument for
        each work item. (non-blocking).

        See Also
        --------
        map
            Blocking version of this method.

        submit
            More flexible interface receiving a generator yielding each work
            item parameters (callable and arguments).
        """
        def work_factory():
            for arg in arg_list:
                yield callable, (arg,), kwargs

        job = self.job_class(work_factory=work_factory)
        return self._submit_job(job)

    def submit(self, work_factory, *args, **kwargs):
        """ Build a Job around the callable+arguments submitted to run.

        Parameters
        ----------
        work_factory : generator
            Callable that defines the job to be executed, by yielding every
            work item in the job.

        args, kwargs : tuple
            Arguments to pass to work_factory.

        Returns
        -------
        2-tuple or None
            Job's id and list of ids for all WorkItems in the job. Returns None
            if job was submitted after the job manager started shutting down.

        See Also
        --------
        async_map
            To submit a job (made of multiple work items) using the Pool style
            interface directly passing the worker callable and the list of
            arguments, one argument for each work item.
        """
        if self._shutting_down:
            msg = "Cannot submit new job because job manager is shutting down."
            logger.warning(msg)
            return

        job = self.job_class(work_factory=work_factory,
                             work_factory_args=(args, kwargs))

        return self._submit_job(job)

    # Other public interface methods ------------------------------------------

    def get_results(self, job_id, work_id=None):
        """ Collect the results from Job with id job_id and optionally work_id.

        Parameters
        ----------
        job_id : str
            ID of the job requested.

        work_id : str
            ID of the work item of the job requested if any. If left to None,
            all work items' results are returned.

        Returns
        -------
        any
            Returns what the job callable returns if the job has finished, or
            None otherwise. Removes that result from the stored results too.


        Raises
        ------
        ValueError
            If the job ID isn't found.

        FIXME: Add a check to the _futures_id_map for jobs that failed with an
        exception.
        """
        msg = "Retrieving results for job {} work {}.".format(job_id, work_id)
        logger.debug(msg)

        if work_id is None:
            results = self._get_job_results(job_id)
        else:
            results = self._get_work_item_results(job_id, work_id)

        return results

    def get_status(self, job_id, work_id=None):
        """ Returns the status for a specific work items.
        """
        id_in_results = (job_id in self._job_results and
                         work_id in self._job_results[job_id])

        if (job_id, work_id) in self._futures_id_map:
            # If we still have access to the future, probe it:
            future = self._futures_id_map[(job_id, work_id)]
            return self._get_status_from_future(future)
        elif id_in_results:
            # Future has finished and has been processed. Inspect the
            # job_results dict
            return self._get_status_from_results(job_id, work_id)
        else:
            msg = 'The job {} work {} was never scheduled or its results' \
                  ' have already been collected.'.format(job_id, work_id)
            logger.exception(msg)
            raise ValueError(msg)

    def wait(self, job_id=None, work_id=None, timeout=None):
        """ Wait until results for the provided job are available.
        """
        if job_id and not work_id:
            msg = "Waiting for job {}".format(job_id)
        elif job_id and work_id:
            msg = "Waiting for job {} and work item {}".format(job_id, work_id)
        else:
            msg = "Waiting for all jobs"

        logger.debug(msg)

        if job_id is None and work_id is None:
            self._wait_for_all_jobs(timeout=timeout)
        elif job_id is not None and work_id is None:
            self._wait_for_job(job_id, timeout=timeout)
        elif job_id is not None and work_id is not None:
            self._wait_for_work_item(job_id, work_id, timeout=timeout)
        else:
            msg = "Waiting for a work item without specifying the job it " \
                  "belongs to is not supported."
            logger.exception(msg)
            raise ValueError(msg)

    def shutdown(self, wait=True):
        """ Shutdown manager, cancelling pending jobs that didn't start.
        """
        logger.info("Shutting down the job manager {}.".format(self.name))
        self._shutting_down = True
        self._request_cancelling_remaining_items()
        self._executor.shutdown(wait=wait)
        self._executor = None

    # Private interface -------------------------------------------------------

    def _request_cancelling_remaining_items(self):
        """ Send a cancel request to all remaining futures.
        """
        remaining_items = list(self._futures_id_map.keys())
        for (job_id, work_id) in remaining_items:
            self._request_cancelling_item(job_id, work_id)

    def _request_cancelling_item(self, job_id, work_id):
        future = self._futures_id_map.get((job_id, work_id), None)
        if future is not None:
            cancellation_result = future.cancel()
            if cancellation_result:
                result = {RESULT_KEY: RESULT_CANCELLED_ITEM}
                with self._state_lock:
                    self._job_results[job_id][work_id] = result
                    self._pending_jobs.remove((job_id, work_id))
                    self._futures_id_map.pop((job_id, work_id))

    def _submit_job(self, job):
        """ Function to process all work items of a job.

        Parameters
        ----------
        job : Instance(Job)
            The job to be submitted.

        Returns
        -------
        2-tuple
            Job's id and list of ids for all WorkItems in the job.
        """
        job_id = job.id
        with self._state_lock:
            self._job_results[job_id] = {}

        # To collect what was created
        work_item_ids = []
        for work_item in job.iter_work_items():
            work_item_id = work_item.id
            work_item_ids.append(work_item_id)
            self._pending_jobs.add((job_id, work_item_id))
            work_func = work_item.work_func
            args, kwargs = work_item.work_func_args
            future = self._executor.submit(work_func, *args, **kwargs)
            # To track work done, add a new attribute
            setattr(future, FUTURE_ATTR_NAME, (job_id, work_item_id))
            self._futures_id_map[(job_id, work_item_id)] = future
            future.add_done_callback(self._work_item_completed)

        msg = "Submitted {} work items for job {}: {}."
        msg = msg.format(len(work_item_ids), job_id, work_item_ids)
        logger.debug(msg)

        return job_id, work_item_ids

    def _work_item_completed(self, future):
        """ Called when a job has completed: updates _job_results,
        _pending_jobs and removes future from _futures_id_map.

        Note: this callback doesn't get called if the future's callable raises
        an exception.

        Subclass to implement more fine-grained error handling if the callable
        returns specific information. For example, could contain information to
        trigger a re-submission of the work item upon (certain) failures.
        """
        job_id, work_id = getattr(future, FUTURE_ATTR_NAME)

        msg = "{}-{} has finished executing.".format(job_id, work_id)
        logger.debug(msg)

        exception = future.exception()
        if exception is not None:
            self._work_item_failed(future)
            return

        result = future.result()
        result[RESULT_KEY] = RESULT_SUCCESSFUL_ITEM
        with self._state_lock:
            self._job_results[job_id][work_id] = result
            self._pending_jobs.remove((job_id, work_id))
            self._futures_id_map.pop((job_id, work_id))

            event = JobManagerEvent(job_id=job_id, work_id=work_id)
            self.work_item_completed = event

    def _work_item_failed(self, future):
        """ Process future that has raised an exception.
        """
        job_id, work_id = future._job_manager_id
        exception = future.exception()

        msg = "{}-{} raised a {} exception: {}."
        msg = msg.format(job_id, work_id, type(exception), exception.args[0])
        logger.debug(msg)

        result = {RESULT_KEY: RESULT_EXCEPTION_ITEM.format(exception)}
        with self._state_lock:
            self._job_results[job_id][work_id] = result
            if (job_id, work_id) in self._pending_jobs:
                self._pending_jobs.remove((job_id, work_id))
            self._futures_id_map.pop((job_id, work_id), None)

            event = JobManagerEvent(job_id=job_id, work_id=work_id)
            self.work_item_completed = event

    def _pending_items_for_job(self, job_id):
        """ Return a *new* set of (job_id, work_id) tuples still pending for a
        specific job_id.
        """
        with self._state_lock:
            remaining_items = {wk for (jb, wk) in self._pending_jobs
                               if jb == job_id}
        return remaining_items

    # Results related private methods -----------------------------------------

    def _get_job_results(self, job_id):
        """ Get the results for all work items of a job if that job finished.
        """
        job_results = self._job_results
        if self._pending_items_for_job(job_id):
            return None
        elif job_id in job_results:
            with self._state_lock:
                return job_results.pop(job_id)

        msg = 'The job {} was not scheduled or its results have already been' \
              ' collected.'.format(job_id)
        logger.exception(msg)
        raise ValueError(msg)

    def _get_work_item_results(self, job_id, work_id):
        """ Get the results for a specific work items, if finished.
        """
        job_results = self._job_results
        if work_id in self._pending_items_for_job(job_id):
            return None
        elif job_id in job_results and work_id in job_results[job_id]:
            return job_results[job_id].pop(work_id)

        msg = 'The job {} work {} was not scheduled or its results have ' \
              'already been collected.'.format(job_id, work_id)
        logger.exception(msg)
        raise ValueError(msg)

    # Wait related private methods --------------------------------------------

    def _wait_for_all_jobs(self, timeout=None):
        start = time()
        while True:
            if not self._pending_jobs:
                return
            sleep(self.wait_sleep_period)
            if timeout is not None and time()-start > timeout:
                msg = "All jobs didn't complete before timeout."
                raise TimeOutError(msg)

    def _wait_for_job(self, job_id, timeout=None):
        start = time()
        while True:
            items_for_job = self._pending_items_for_job(job_id)
            if not items_for_job:
                return
            sleep(self.wait_sleep_period)
            if timeout is not None and time()-start > timeout:
                msg = "Job {} didn't complete before timeout.".format(job_id)
                raise TimeOutError(msg)

    def _wait_for_work_item(self, job_id, work_id, timeout=None):
        start = time()
        while True:
            if (job_id, work_id) not in self._pending_jobs:
                return
            sleep(self.wait_sleep_period)
            if timeout is not None and time()-start > timeout:
                msg = "Job {} work {} didn't complete before timeout."
                msg = msg.format(job_id, work_id)
                raise TimeOutError(msg)

    # Status related private methods ------------------------------------------

    def _get_status_from_results(self, job_id, work_id):
        """ Inspect the job_results dict, and infer job status.

        This assumes that the job_results dict has been updated with the
        requested job. Raises a KeyError otherwise.
        """
        result = self._job_results[job_id][work_id]
        if result[RESULT_KEY] == RESULT_CANCELLED_ITEM:
            return CANCELLED_STATUS
        elif result[RESULT_KEY].startswith("ITEM FAILED"):
            return RAN_FAILED_STATUS
        else:
            return RAN_SUCCESSFULLY_STATUS

    def _get_status_from_future(self, future):
        """ Inquire the status of the future object. Update results dicts if
        future raised an exception.
        """
        if future.running():
            return RUNNING_STATUS
        if future.cancelled():
            return CANCELLED_STATUS
        if future.done() and future.exception():
            self._work_item_failed(future)
            return RAN_FAILED_STATUS
        if future.done() and future.result():
            return RAN_SUCCESSFULLY_STATUS
        return PENDING_STATUS

    # HasTraits methods -------------------------------------------------------

    def _job_class_default(self):
        from .job import Job
        return Job

    def _max_workers_default(self):
        return multiprocessing.cpu_count()

    def __executor_default(self):
        """ Initialize the executor.
        """
        import concurrent.futures
        klass = getattr(concurrent.futures, self._executor_klass)

        msg = "Job manager's executor: {} with {} max workers."
        logger.debug(msg.format(klass, self.max_workers))

        _executor = klass(max_workers=self.max_workers)
        return _executor
