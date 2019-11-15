import os
from os.path import isfile, join
from contextlib import contextmanager
from tempfile import mkdtemp
from shutil import rmtree

from traits.api import pop_exception_handler, push_exception_handler

DEFAULT_TEMP_FILENAME = "tempfile.temp"


@contextmanager
def reraise_traits_notification_exceptions():
    """Context where traits notification exceptions are re-raised temporarily.

    Traits tends to swallow errors in notification handlers. This temporarily
    changes the exception to reraise.

    When testing for exceptions, note that using a `@nose.tools.raise`
    decorator will not work since the exception handler is changed on exit.
    Instead use `nose.tools.assert_raises` as a context manager.
    """
    push_exception_handler(lambda *args: None, reraise_exceptions=True)
    try:
        yield
    finally:
        pop_exception_handler()


@contextmanager
def temp_fname(fname="", target_dir=None):
    """ Temporarily create a filename and remove after use.

    By default, the file is created in the current directory by the target_dir
    argument allows to place it anywhere else.

    Parameters
    ----------
    fname : str
        Name of the target temporary file.

    target_dir : str
        Directory path on the filesystem inside which the target filename will
        be.
    """
    if target_dir is None:
        target_dir = os.curdir

    if fname == "":
        fname = DEFAULT_TEMP_FILENAME

    fpath = join(target_dir, fname)
    if isfile(fpath):
        os.remove(fpath)

    try:
        yield fpath
    finally:
        if isfile(fpath):
            os.remove(fpath)


@contextmanager
def temp_folder():
    """ Context manager that returns temp folder that will be detroyed on exit.
    """
    temp_dir = mkdtemp()
    try:
        yield temp_dir
    finally:
        rmtree(temp_dir)


@contextmanager
def revert_changes_to_text_file(filepath):
    """ Revert any changes to an existing text file after use.
    """
    initial_content = open(filepath, 'r').read()
    try:
        yield
    finally:
        open(filepath, 'w').write(initial_content)


@contextmanager
def temp_bringup_ui_for(obj, kind=None):
    """ Create UI and temporarily bring it up to allow operations while it's up
    """
    ui = obj.edit_traits(kind=kind)
    try:
        yield ui
    finally:
        ui.dispose()


def assert_obj_gui_works(obj, kind=None):
    """ Make sure an object's TraitsUI can be built and visualized.
    """
    ui = obj.edit_traits(kind=kind)
    ui.dispose()


def wrap_chaco_plot(plot):
    from traits.api import HasTraits, Instance
    from traitsui.api import UItem, View
    from chaco.api import BasePlotContainer
    from enable.api import ComponentEditor

    class ViewPlot(HasTraits):
        """ Quick class to embed a Chaco plot in a Traits class to force it to
        be drawn.

        This can be useful to test plot properties that are only initialized
        when being drawn.

        Examples
        --------
        >>> with temp_bringup_ui_for(ViewPlot(plot=plot)):
        ...     assert plot.x_axis.ticklabel_cache == []
        """
        plot = Instance(BasePlotContainer)
        view = View(
            UItem("plot", editor=ComponentEditor()),
            resizable=True
        )

    return ViewPlot(plot=plot)
