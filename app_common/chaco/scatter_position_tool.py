""" Overlay to display the coordinate of a scatter point hovered over.
"""
import logging
import pandas as pd

from traits.api import Bool, Callable, Float, Instance, List, on_trait_change,\
    Str
from chaco.api import TextBoxOverlay
from chaco.scatterplot import ScatterPlot
from app_common.chaco.scatter_inspector import ScatterInspector

logger = logging.getLogger(__name__)


def add_scatter_inspectors(plot, datasets=None, include_overlay=True,
                           threshold=5, **kwargs):
    """ Add scatter data inspector tools and optional text overlay to plot.

    The purpose is to be able to display interactively the position of each
    point of the renderers contained in an OverlayPlotContainer.

    An inspector per renderer will be created, to listen to mouse hover events
    on all data points. But there is no need for multiple overlays: a single
    one can listen to all inspectors.

    Parameters
    ----------
    plot : chaco OverlayPlotContainer
        Chaco plot containing the renderers to add scatter inspectors.

    datasets : list
        List of dataframes containing the data displayed in each renderer.

    include_overlay : bool
        Whether to include the overlay.

    threshold : int
        The threshold, in pixels, around the cursor location to search for
        points. (Passed to the chaco ScatterInspector.)
    """
    inspectors = []

    if isinstance(datasets, pd.DataFrame):
        datasets = [datasets]
    elif datasets is None:
        try:
            datasets = [pd.DataFrame(plot.data.arrays)]
        except AttributeError as e:
            msg = "AttributeError raised: if the provided plot doesn't own a" \
                  " 'data' attribute with an ArrayPlotData containing all " \
                  "the data, the datasets must be explicitly provided. " \
                  "(Error was: '{}')".format(e)
            logger.exception(msg)
            raise ValueError(msg)

    assert len(datasets) == len(plot.components)

    for data, renderer in zip(datasets, plot.components):
        if not isinstance(renderer, ScatterPlot):
            continue

        # Create the inspector tool if not already present: otherwise, the
        # mouse event might be marked handled before updating the text overlay
        inspector = None
        for tool in renderer.tools:
            if isinstance(tool, ScatterInspector):
                inspector = tool
                if inspector.data is None:
                    inspector.data = data

        if inspector is None:
            inspector = DataframeScatterInspector(component=renderer,
                                                  data=data,
                                                  threshold=threshold)
            renderer.tools.append(inspector)

        inspectors.append(inspector)

    # Create and attach the inspector overlay
    if include_overlay:
        overlay = DataframeScatterOverlay(plot, inspectors=inspectors,
                                          **kwargs)
        plot.overlays.append(overlay)
    else:
        overlay = None

    return inspectors, overlay


class DataframeScatterInspector(ScatterInspector):

    data = Instance(pd.DataFrame)


class DataframeScatterOverlay(TextBoxOverlay):
    """ Overlay for displaying information from a DataInspectorTool.
    """

    #: The inspector tool(s) which trigger hover events
    inspectors = List(Instance(DataframeScatterInspector))

    #: Function which takes an inspector and an index and returns info string
    message_for_data = Callable

    bgcolor = Str("black")

    alpha = Float(0.6)

    text_color = Str("white")

    border_color = "none"

    include_index = Bool

    @on_trait_change('inspectors:inspector_event')
    def scatter_point_found(self, inspector, name, event):
        data_idx = event.event_index
        if data_idx is not None:
            self.text = self.message_for_data(inspector, data_idx)
        else:
            self.text = ""

        self.visible = len(self.text) > 0
        self.component.request_redraw()

    def _message_for_data_default(self):
        def show_data(inspector, data_idx):
            data = inspector.data.iloc[data_idx]
            if self.include_index:
                elements = ["idx: {}".format(data_idx)]
            else:
                elements = []

            for col in data.index:
                elements.append("{}: {}".format(col, data[col]))
            return "\n".join(elements)
        return show_data


if __name__ == "__main__":
    from chaco.api import Plot, ArrayPlotData
    from traits.api import HasTraits, Instance
    from traitsui.api import View, Item
    from enable.api import ComponentEditor
    import numpy as np

    def _create_plot_component():
        # Create a random scattering of XY pairs
        x = np.random.uniform(0.0, 10.0, 50)
        y = np.random.uniform(0.0, 5.0, 50)
        data = pd.DataFrame({"x": x, "y": y,
                             "dataset": np.random.choice(list("abcdefg"), 50)})

        plot_data = ArrayPlotData(x=data["x"], y=data["y"],
                                  dataset=data["dataset"])
        plot = Plot(plot_data)
        plot.plot(("x", "y"), type="scatter")

        add_scatter_inspectors(plot)
        return plot

    class Test(HasTraits):
        plot = Instance(Plot)
        view = View(Item("plot", editor=ComponentEditor(size=(900, 500)),
                         show_label=False),
                    resizable=True, title="Tooltip demo")

        def _plot_default(self):
            return _create_plot_component()

    Test().configure_traits()
