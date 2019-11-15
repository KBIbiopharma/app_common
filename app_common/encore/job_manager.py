""" Base job manager class that can schedule and execute jobs (asynchronously).
"""
from abc import abstractmethod
import logging

from traits.api import Bool, HasStrictTraits, Str

logger = logging.getLogger(__name__)


class JobManager(HasStrictTraits):
    """ Manages execution of jobs.
    """
    #: Optional string to identify each job manager instances.
    name = Str

    #: The job manager is ready to accept job requests
    started = Bool(False)

    @abstractmethod
    def get_results(self, job_id):
        """ Get the results from the execution of job specified by `job_id`.

        Parameters
        ----------
        job_id : string
            The unique id for the job whose results are requested..

        Returns
        -------
        results : dict or None
            dict, if the job is completed or None.
            The keys of the dict are the unique ids assigned to each of the
            worker items and the value is the return value from the execution
            of the work item.

        NOTE: A *completed* job can be queried only once. Subsequent queries
        will raise a `ValueError`.
        """

    @abstractmethod
    def submit(self, work_factory, *args, **kwargs):
        """ Submit a job.

        Parameters
        ----------
        work_factory : callable
            A callable that returns a generator expression for the work items.
        args : tuple
            positional arguments to be passed to `work_factory`.
        kwargs : dict
            keyword arguments to be passed to `work_factory`.

        Returns
        -------
        job_id : string
            A unique id for the submitted job. The results from the job
            execution can be queried as `get_result(job_id)`.
        """

    @abstractmethod
    def wait(self):
        """ Wait until all scheduled jobs are completed.
        """

    def start(self):
        """ Start accepting requests for job execution.
        """
        self.started = True

    @abstractmethod
    def shutdown(self):
        """ Shutdown the manager and release resources.
        """
