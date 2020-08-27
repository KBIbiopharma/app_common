from datetime import datetime
from numpy import array, isnan, nan, nanmean

from pyface.tasks.api import TraitsDockPane
from traits.api import Button, Enum, Float, HasStrictTraits, Instance, Int, \
    List, Property, Str
from traits.trait_base import _Undefined
from traitsui.api import HGroup, Item, View, Spring, TableEditor, VGroup
from traitsui.table_column import ObjectColumn, NumericColumn

from ..encore.simple_async_job_manager import ALL_STATUS, SimpleAsyncJobManager
from ..encore.job import WORK_ITEM_ID_PREFIX

JM_STATE_RUNNING = "Running..."

JM_STATE_IDLE = "Idle"

NUM_VALUE_TO_AVERAGE = 3


class JobResultDescription(HasStrictTraits):
    """ Utility class to display job results in a table.
    """
    #: Job ID (unique)
    id = Str

    #: Job type/nature
    type = Str

    #: Status of the job after running: success, failure, ...
    status = Enum(ALL_STATUS)

    #: How much time the job took
    run_time = Float

    #: Formatted datetime when the job finished
    finished_at = Str


def build_pending_job_table_editor(display_type=False, display_run_time=False,
                                   run_time_fmt="%s"):
    """ Build a table editor to display a list of JobResultDescription.

    Parameters
    ----------
    display_type : bool [OPTIONAL, default=False]
        Whether to include the job type column. Useful if the manager handles
        job of multiple types.

    display_run_time : bool [OPTIONAL, default=False]
        Whether to display the run time attribute of the JobResultDescription.

    run_time_fmt : str
        Formatting to use for the run_time numeric column. Ignored if
        display_run_time is False.
    """
    columns = [
        ObjectColumn(name="finished_at", label='Job end time',
                     style="readonly"),
        ObjectColumn(name='id', label='Job ID', style="readonly"),
        ObjectColumn(name='status', label='Status', style="readonly"),
    ]
    if display_type:
        type_col = ObjectColumn(name='type', label='Type', style="readonly")
        columns.insert(1, type_col)

    if display_run_time:
        run_time_col = NumericColumn(name="run_time", label="Run time (s)",
                                     style="readonly", format=run_time_fmt)
        columns.append(run_time_col)

    editor = TableEditor(columns=columns, deletable=False, auto_size=True,
                         sortable=True, editable=False)
    return editor


class JobManagerPane(TraitsDockPane):
    """ View on a JobManager object.
    """

    # -------------------------------------------------------------------------
    # 'TaskPane' interface
    # -------------------------------------------------------------------------

    id = 'common.job_manager_pane'

    name = 'Job Manager'

    # -------------------------------------------------------------------------
    # PerformanceParamPane
    # -------------------------------------------------------------------------

    #: Job Manager monitored
    job_manager = Instance(SimpleAsyncJobManager)

    num_pending_jobs = Property(Int,
                                depends_on='job_manager:_pending_jobs')

    #: List of metatadata about the results returned by each job
    job_results = List(JobResultDescription)

    #: Button to empty the results list and clear the table
    clear_results_button = Button("Clear results")

    #: If the result dict contains a key with the job run time, that can be
    # used to compute
    run_time_result_key = Str

    #: Number of jobs already run since the application launch
    num_run_work_items = Int

    #: String description of the state of the job manager: running or idle?
    job_manager_state = Property(Enum([JM_STATE_IDLE, JM_STATE_RUNNING]),
                                 depends_on='num_pending_jobs')

    #: Amount of time to finish the currently pending jobs
    eta = Property(Str, depends_on="num_pending_jobs, avg_job_duration")

    #: Last N run times to compute an average run time for a simulation
    last_run_times = List

    #: Average runtime recently
    avg_job_duration = Property(Float, depends_on="last_run_times[]")

    # -------------------------------------------------------------------------
    # HasTraits interface
    # -------------------------------------------------------------------------

    def __init__(self, **traits):
        super(JobManagerPane, self).__init__(**traits)
        # Because it deals with a multi-threaded tool, this way of adding the
        # listener is safer because it can be removed when preparing to destroy
        self.on_trait_change(self.update_job_result_list,
                             "job_manager.work_item_completed")

    def prepare_destroy(self):
        self.on_trait_change(self.update_job_result_list,
                             "job_manager.work_item_completed", remove=True)

    def traits_view(self):
        """ The view used to construct the dock pane's widget.
        """
        display_run_time = bool(self.run_time_result_key)
        job_table = build_pending_job_table_editor(
            display_type=False, run_time_fmt="%.2f",
            display_run_time=display_run_time
        )

        view = View(
            VGroup(
                VGroup(
                    HGroup(
                        Item("job_manager_state", style="readonly",
                             label="State"),
                        Spring(),
                        Item("num_run_work_items", style="readonly",
                             label="Num. run jobs"),
                        Spring(),
                        Item("object.job_manager.max_workers",
                             style="readonly", label="Num. workers"),
                    ),
                    HGroup(
                        Item("num_pending_jobs", style="readonly",
                             label="Num. pending jobs"),
                        Spring(),
                        Item("eta", style="readonly",
                             label="Estim. ETA", visible_when=""),
                    ),
                    show_border=True, label="Manager status"
                ),
                VGroup(
                    Item('job_results', show_label=False, editor=job_table),
                    Item("clear_results_button", show_label=False),
                    show_border=True, label="Job results"
                ),
            ),
            resizable=True
        )
        return view

    # Traits property getters/setters -----------------------------------------

    def update_job_result_list(self, event):
        """ A work item finished running: collect information into job_results.
        """
        if isinstance(event, _Undefined):
            return

        job_id, work_id = event.job_id, event.work_id
        results = self.job_manager._job_results[job_id][work_id]
        if self.run_time_result_key:
            run_time = results.get(self.run_time_result_key, nan)
        status = self.job_manager.get_status(job_id, work_id)
        prefix_len = len(WORK_ITEM_ID_PREFIX)
        job_id_str = work_id[prefix_len: prefix_len+7] + "..."
        returned_at = datetime.now().strftime("%y/%m/%d-%H:%M:%S")
        desc = JobResultDescription(id=job_id_str, status=status,
                                    run_time=run_time, type="cadet",
                                    finished_at=returned_at)
        self.job_results.append(desc)
        # Remember how many jobs have run, even if the job_results list gets
        # cleared:
        self.num_run_work_items += 1
        if self.run_time_result_key:
            self.update_run_times(run_time)

    def update_run_times(self, run_time):
        self.last_run_times.pop(0)
        self.last_run_times.append(run_time)

    # Traits property getters/setters -----------------------------------------

    def _get_num_pending_jobs(self):
        if self.job_manager is None:
            return 0
        return len(self.job_manager._pending_jobs)

    def _get_avg_job_duration(self):
        if not self.last_run_times:
            return nan

        avg_job_duration = nanmean(array(self.last_run_times))
        return avg_job_duration

    def _get_eta(self):
        job_duration = self.avg_job_duration
        if isnan(job_duration) or self.num_pending_jobs == 0:
            return ""

        div, mod = divmod(self.num_pending_jobs, self.job_manager.max_workers)
        effective_num_jobs = div + 1 * int(mod > 0)
        eta_in_sec = job_duration * effective_num_jobs
        if eta_in_sec > 3700:
            eta = eta_in_sec / 3600.
            unit = "h"
        elif eta_in_sec > 70:
            eta = eta_in_sec / 60.
            unit = "min"
        else:
            eta = eta_in_sec
            unit = "sec"

        return "{:.1f} {}".format(eta, unit)

    def _get_job_manager_state(self):
        if self.num_pending_jobs:
            return JM_STATE_RUNNING
        else:
            return JM_STATE_IDLE

    # Traits listeners --------------------------------------------------------

    def _clear_results_button_fired(self):
        self.job_results = []

    # Traits initialization methods -------------------------------------------

    def _last_run_times_default(self):
        return [nan] * NUM_VALUE_TO_AVERAGE
