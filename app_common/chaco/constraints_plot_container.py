""" Constraint based plot container. Requires Enable 4.6.0+ and kiwisolver,
which currently doesnt have a released version that supports Python3.
"""

from traits.api import Instance, Str, Tuple
from enable.api import ConstraintsContainer
from chaco.plot_component import DEFAULT_DRAWING_ORDER


class ConstraintsPlotContainer(ConstraintsContainer):
    """ Replaces BasePlotContainer. """

    # Redefine the container layers to name the main layer as "plot" instead
    # of the Enable default of "mainlayer"
    container_under_layers = Tuple("background", "image", "underlay", "plot")

    # Duplicate trait declarations from PlotComponent.  We don't subclass
    # PlotComponent to avoid MRO complications with trait handlers and property
    # getters/setters.

    draw_order = Instance(list, args=(DEFAULT_DRAWING_ORDER,))
    draw_layer = Str("plot")
