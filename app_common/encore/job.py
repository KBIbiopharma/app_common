from uuid import uuid4
from sys import version_info

from traits.api import (
    Callable, Dict, HasStrictTraits, Int, ReadOnly, Str, Tuple
)

JOB_ID_PREFIX = "Job "

WORK_ITEM_ID_PREFIX = "Work item "


class WorkItem(HasStrictTraits):
    """ Unit of work a job manager will have to schedule and get executed.
    """
    #: Unique identifier for the work item.
    id = ReadOnly(Str)

    #: The `id` corresponding to the job that spawned this work item.
    job_id = Str

    #: A callable that performs the work for the current work item.
    work_func = Callable

    #: A tuple containing the `args` and `kwargs` arguments to `work_func`
    work_func_args = Tuple(Tuple, Dict)

    def _id_default(self):
        return WORK_ITEM_ID_PREFIX + str(uuid4())


class Job(HasStrictTraits):
    """ Base class for a logical group of work items to be completed.
    """

    #: Unique identifier for the job.
    # Don't use ReadOnly because MultiProc executor pickles these Jobs to send
    # to worker.
    id = Str

    #: The priority level for the current job.
    priority = Int

    #: User visible name for the current job.
    name = Str

    #: User visible description for the current job.
    description = Str

    #: A callable that returns a generator expression for the work items.
    work_factory = Callable

    #: A tuple containing the `args` and `kwargs` arguments to `work_func`
    work_factory_args = Tuple(Tuple, Dict)

    def _id_default(self):
        return JOB_ID_PREFIX + str(uuid4())

    def iter_work_items(self):
        """ Return a generator expression for the work items, wrapping the
        callable with a try/except and returning a status dictionary containing
        a run status and the job and work id of the job.
        """
        args, kwargs = self.work_factory_args
        work_iter = self.work_factory(*args, **kwargs)
        while True:
            if version_info.major > 2:
                func, func_args, func_kwargs = work_iter.__next__()
            else:
                func, func_args, func_kwargs = work_iter.next()

            yield WorkItem(
                job_id=self.id,
                work_func=func,
                work_func_args=(func_args, func_kwargs)
            )
