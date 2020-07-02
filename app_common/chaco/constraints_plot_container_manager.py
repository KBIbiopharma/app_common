import logging

from traits.api import Any, Bool, Dict, Enum, HasStrictTraits, Instance, Int
from chaco.base_plot_container import BasePlotContainer
from enable.layout.api import align, vbox, hbox, grid

from app_common.chaco.constraints_plot_container import \
    ConstraintsPlotContainer

LAYOUT_MAPS = {"horizontal": hbox, "vertical": vbox, "grid": grid}

logger = logging.getLogger(__name__)


class ConstraintsPlotContainerManager(HasStrictTraits):
    """ Manager of a constraints plot container.
    """

    #: The collection of Plots in the container. Each Plot is mapped to a key
    #: for caching, and hide/show purposes.
    plot_map = Dict

    #: Remove a Plot from the container if there are no curves being rendered.
    #: Set to `False` to avoid the resizing of the Plots in the container
    #: when the empty Plot is removed.
    remove_empty_plot = Bool(True)

    #: The instance of PlotContainer that contains all the Plots.
    container = Instance(ConstraintsPlotContainer)

    # Container layout parameters ---------------------------------------------

    #: Stack components into a horizontal box, vertical box, or a grid?
    layout_type = Enum(["horizontal", "vertical", "grid"])

    # In-between plot padding parameters --------------------------------------

    layout_spacing = Int(60)

    layout_margins = Int(60)

    # Outer container padding parameters --------------------------------------

    padding_top = Int(0)

    padding_bottom = Int(5)

    padding_left = Int(10)

    padding_right = Int(10)

    def init(self):
        """ Initialize the plots.
        """
        self._create_container()

    # ConstraintsPlotContainerManager public interface ------------------------

    def refresh_container(self, force=False):
        if force:
            self.container.invalidate_and_redraw()
        else:
            self.container.request_redraw()

    def add_plot(self, plot_key, plot, position=None):
        """ Add new Plot to container, or update if key already exists.
        """
        if position is None:
            position = len(self.plot_map)
            self.container.add(plot)
        else:
            self.container.insert(position, plot)

        self.plot_map[plot_key] = (plot, position)
        self.refresh_container()

    def delete_plot(self, plot_key, plot):
        """ Remove Plot to container.
        """
        self.plot_map.pop(plot_key)
        self.container.remove(plot)
        self.refresh_container()

    def hide_plot(self, plot_key):
        """ Retrieve Plot for specific log type if exists, create  it otherwise
        """
        result = self.plot_map.get(plot_key, None)
        if result is None:
            msg = "Plot key requested ({}) not in cache".format(plot_key)
            logger.error(msg)
            raise ValueError(msg)

        plot, position = result
        self.container.remove(plot)
        self.refresh_container()

    def show_plot(self, plot_key):
        """ Retrieve Plot for specific log type if exists, create  it otherwise
        """
        result = self.plot_map.get(plot_key, None)
        if result is None:
            msg = "Plot key requested ({}) not in cache".format(plot_key)
            logger.error(msg)
            raise ValueError(msg)

        plot, position = result
        self.container.insert(position, plot)
        self.refresh_container()

    def _create_container(self):
        self.container = container = ConstraintsPlotContainer(
            bgcolor='transparent',
            padding_top=self.padding_top,
            padding_bottom=self.padding_bottom,
            padding_left=self.padding_left,
            padding_right=self.padding_right
        )
        container.layout_constraints = self._get_layout

    def _get_layout(self, container):
        """ Returns a list of constraints that is meant to be passed to
        a ConstraintsContainer.
        """
        constraints = []

        # NOTE: inequality expressions seem a lil shaky in that it requires
        # some tweaking to finding a set of constraints that works well !
        # But this is much better than manually tweaking padding etc.

        # Another option is to simply calculate the values of the height etc
        # and set it as simple inequalities (as opposed to using height as
        # another variable in the expressions)

        # FIXME: also, the layouts can prob. be specified as input similar to
        # the other plot properties.

        # split components into groups. For now, just UV and others
        components = container.components

        # NOTE: looks like every comp in the container needs a constraint,
        # else they get messed up or ignored.

        # create an ordered (top to bottom) list of components
        layout_helper = LAYOUT_MAPS[self.layout_type]
        constraints.extend([
            layout_helper(*components, spacing=self.layout_spacing,
                          margins=self.layout_margins),
            # align widths of all components to be the same
            align('layout_width', *components),
            # align heights of *other* components to be the same
            align('layout_height', *components),
        ])
        return constraints
