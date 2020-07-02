""" Extended renderer factories.
"""
import logging

from numpy import arange, array, linspace, ndarray
from chaco.api import AbstractDataSource, ArrayDataSource, \
    ColormappedScatterPlot, CMapImagePlot, ContourLinePlot, \
    DataRange2D, DataRange1D, GridDataSource, GridMapper, ImagePlot, jet, \
    LinearMapper, Spectral
from chaco.plot_factory import add_default_grids, add_default_axes
from chaco.image_data import ImageData

logger = logging.getLogger(__name__)


def create_line_plot(index_mapper_class=LinearMapper, **kwargs):
    """ Expand chaco implementation.

    Remove when https://github.com/enthought/chaco/pull/514 is merged and in
    use.
    """

    from chaco.plot_factory import create_line_plot

    alpha = kwargs.pop("alpha", None)
    renderer = create_line_plot(**kwargs)
    if not isinstance(renderer.index_mapper, index_mapper_class):
        renderer.index_mapper = index_mapper_class(
            range=renderer.index_mapper.range
        )
    if alpha:
        renderer.alpha = alpha
    return renderer


def create_scatter_plot(index_mapper_class=LinearMapper,
                        value_mapper_class=LinearMapper, **kwargs):
    """ Expand chaco implementation.

    Remove when https://github.com/enthought/chaco/pull/514 is merged and in
    use.
    """
    from chaco.plot_factory import create_scatter_plot

    alpha = kwargs.pop("alpha", None)
    renderer = create_scatter_plot(**kwargs)
    if not isinstance(renderer.index_mapper, index_mapper_class):
        renderer.index_mapper = index_mapper_class(
            range=renderer.index_mapper.range
        )

    if not isinstance(renderer.value_mapper, value_mapper_class):
        renderer.value_mapper = value_mapper_class(
            range=renderer.value_mapper.range
        )

    if alpha:
        renderer.alpha = alpha
    return renderer


def create_bar_plot(index_mapper_class=LinearMapper, **kwargs):
    """ Expand chaco implementation.

    Remove when https://github.com/enthought/chaco/pull/514 is merged and in
    use.
    """
    from chaco.plot_factory import create_bar_plot

    alpha = kwargs.pop("alpha", None)
    renderer = create_bar_plot(**kwargs)
    if not isinstance(renderer.index_mapper, index_mapper_class):
        renderer.index_mapper = index_mapper_class(
            range=renderer.index_mapper.range
        )
    if alpha:
        renderer.alpha = alpha
    return renderer


def create_cmap_scatter_plot(data=None, index_bounds=None, value_bounds=None,
                             index_mapper_class=LinearMapper,
                             value_mapper_class=LinearMapper,
                             color_bounds=None, color_mapper=jet,
                             orientation="h", marker="circle", marker_size=4,
                             bgcolor="transparent", outline_color="black",
                             border_visible=True,
                             add_grid=False, add_axis=False,
                             index_sort="none", **kwargs):
    """ Creates a ScatterPlot from a single Nx3 data array or a tuple of
    three length-N 1-D arrays.  The data must be sorted on the index if any
    reverse-mapping tools are to be used.

    Pre-existing "index", "value" and color_data datasources can be passed in.

    Parameters
    ----------
    color_mapper : callable, optional
        Function that receives a DataRange1D and returns a ColorMapper
        instance. Defaults to chaco.default_colormaps.jet().
    """
    if len(data) == 3:
        index, value, color_data = _create_data_sources(data)
    elif len(data) > 4 or len(data) < 3:
        msg = "Colormapped marker/segment plots require (index, value, color)"\
              "or (index, value, color, width) data"
        logger.exception(msg)
        raise ValueError(msg)
    elif len(data) == 4:
        index, value, color_data, size = _create_data_sources(data)
        msg = "Size arrays not implemented yet."
        logger.exception(msg)
        raise NotImplementedError(msg)

        # size_range = DataRange1D()
        # size_range.add(size)
        # size_min = kwargs.pop("size_min", 1)
        # size_max = kwargs.pop("size_max", 10)
        #
        # sizemap = LinearMapper(low_pos=size_min, high_pos=size_max,
        #                        range=size_range)

    if index_bounds is not None:
        index_range = DataRange1D(low=index_bounds[0], high=index_bounds[1])
    else:
        index_range = DataRange1D()
    index_range.add(index)
    index_mapper = index_mapper_class(range=index_range)

    if value_bounds is not None:
        value_range = DataRange1D(low=value_bounds[0], high=value_bounds[1])
    else:
        value_range = DataRange1D()
    value_range.add(value)
    value_mapper = value_mapper_class(range=value_range)

    if color_bounds is not None:
        color_range = DataRange1D(low=color_bounds[0], high=color_bounds[1])
    else:
        color_range = DataRange1D()

    color_range.add(color_data)
    color_mapper = color_mapper(color_range)

    plot = ColormappedScatterPlot(index=index, value=value,
                                  color_data=color_data,
                                  index_mapper=index_mapper,
                                  value_mapper=value_mapper,
                                  color_mapper=color_mapper,
                                  orientation=orientation,
                                  marker=marker,
                                  marker_size=marker_size,
                                  bgcolor=bgcolor,
                                  outline_color=outline_color,
                                  border_visible=border_visible, **kwargs)

    # if len(data) == 4:
    #     plot.width_data = size
    #     plot.width_mapper = sizemap
    #     plot.width_by_data = True

    if add_grid:
        add_default_grids(plot, orientation)
    if add_axis:
        add_default_axes(plot, orientation)
    return plot


def create_contour_plot(data=None, contour_type="line", xbounds=None,
                        ybounds=None, levels=None, widths=None,
                        origin='bottom left', orientation="h",
                        index_mapper_class=LinearMapper,
                        value_mapper_class=LinearMapper, **styles):
    # Create the index and add its datasources to the appropriate ranges
    xs = _process_2d_bounds(xbounds, data, 1, cell_plot=False)
    ys = _process_2d_bounds(ybounds, data, 0, cell_plot=False)

    index = GridDataSource(xs, ys, sort_order=('ascending', 'ascending'))
    range2d = DataRange2D()
    range2d.add(index)
    if index_mapper_class == LinearMapper:
        x_type = "linear"
    else:
        x_type = "log"

    if value_mapper_class == LinearMapper:
        y_type = "linear"
    else:
        y_type = "log"

    mapper = GridMapper(x_type=x_type, y_type=y_type, range=range2d)

    value_ds = ImageData(data=data, value_depth=1)

    plot = ContourLinePlot(index=index,
                           value=value_ds,
                           index_mapper=mapper,
                           orientation=orientation,
                           origin=origin,
                           **styles)

    return plot


def create_img_plot(data=None, colormap=None, xbounds=None, ybounds=None,
                    origin='bottom left', orientation="h",
                    index_mapper_class=LinearMapper,
                    value_mapper_class=LinearMapper, **styles):
    """ Create an ImagePlot renderer to represent the provided data.
    """
    if not isinstance(data, ndarray) or len(data.shape) != 2:
        msg = "Received a {}. create_img_plot expects a 2D numpy array to " \
              "make a cmap image plot.".format(type(data))
        logger.exception(msg)
        raise ValueError(msg)

    # Create the index and add its datasources to the appropriate ranges
    xs = _process_2d_bounds(xbounds, data, 1, cell_plot=True)
    ys = _process_2d_bounds(ybounds, data, 0, cell_plot=True)

    value = ImageData(data=data, value_depth=1)

    if colormap is None:
        colormap = Spectral(DataRange1D(value))
    else:
        colormap = colormap(DataRange1D(value))

    index = GridDataSource(xs, ys, sort_order=('ascending', 'ascending'))
    range2d = DataRange2D()
    range2d.add(index)
    if index_mapper_class == LinearMapper:
        x_type = "linear"
    else:
        x_type = "log"

    if value_mapper_class == LinearMapper:
        y_type = "linear"
    else:
        y_type = "log"

    mapper = GridMapper(x_type=x_type, y_type=y_type, range=range2d)

    if len(data.shape) == 3:
        cls = ImagePlot
    else:
        cls = CMapImagePlot

    plot = cls(index=index,
               value=value,
               index_mapper=mapper,
               orientation=orientation,
               origin=origin,
               value_mapper=colormap,
               **styles)

    return plot


def _process_2d_bounds(bounds, array_data, axis, cell_plot=True):
    """Transform an arbitrary bounds definition into a linspace.

    Process all the ways the user could have defined the x- or y-bounds
    of a 2d plot and return a linspace between the lower and upper
    range of the bounds.

    Parameters
    ----------
    bounds : any
        User bounds definition

    array_data : 2D array
        The 2D plot data

    axis : int
        The axis along which the bounds are to be set

    cell_plot : bool
        Is the data plotted at the vertices or in the cells bounded by
        the grid (eg. contour plot vs. image plot)
    """

    if cell_plot:
        num_ticks = array_data.shape[axis] + 1
    else:
        num_ticks = array_data.shape[axis]

    if bounds is None:
        return arange(num_ticks)

    elif isinstance(bounds, tuple):
        # create a linspace with the bounds limits
        return linspace(bounds[0], bounds[1], num_ticks)

    elif isinstance(bounds, ndarray) and bounds.ndim == 1:
        if len(bounds) != num_ticks:
            # bounds is 1D, but of the wrong size
            msg = ("1D bounds of an image plot needs to have 1 more "
                   "element than its corresponding data shape, because "
                   "they represent the locations of pixel boundaries.")
            raise ValueError(msg)
        else:
            return bounds


def _create_data_sources(data, index_sort="none"):
    """
    Returns datasources for index and value based on the inputs.  Assumes that
    the index data is unsorted unless otherwise specified.
    """
    # if not isinstance(data, ndarray) and (len(data) < 2):
    #     raise RuntimeError("Unable to create datasources.")

    index = data[0]

    if type(index) in (list, tuple, ndarray):
        index = ArrayDataSource(array(index), sort_order=index_sort)
    elif not isinstance(index, AbstractDataSource):
        msg = "Need an array or list of values or a DataSource, got {} " \
              "instead.".format(type(index))
        raise RuntimeError(msg)

    if len(data) == 1:
        return index

    value = data[1]
    if type(value) in (list, tuple, ndarray):
        value = ArrayDataSource(array(value))
    elif not isinstance(value, AbstractDataSource):
        msg = "Need an array or list of values or a DataSource, got {} " \
              "instead.".format(type(value))
        raise RuntimeError(msg)

    if len(data) == 2:
        return index, value

    if len(data) >= 3:
        adtl_data1 = data[2]

        if type(adtl_data1) in (list, tuple, ndarray):
            adtl_data1 = ArrayDataSource(array(adtl_data1))
        elif not isinstance(value, AbstractDataSource):
            msg = "Need an array or list of values or a DataSource, got {} " \
                  "instead.".format(type(adtl_data1))
            raise RuntimeError(msg)

        if len(data) == 3:
            return index, value, adtl_data1

    if len(data) == 4:
        adtl_data2 = data[3]

        if type(adtl_data2) in (list, tuple, ndarray):
            adtl_data2 = ArrayDataSource(array(adtl_data2))
        elif not isinstance(value, AbstractDataSource):
            msg = "Need an array or list of values or a DataSource, got {} " \
                  "instead.".format(type(adtl_data2))
            raise RuntimeError(msg)

        return index, value, adtl_data1, data[3]


if __name__ == "__main__":
    from chaco.api import ArrayPlotData, OverlayPlotContainer, Plot
    from traits.api import HasTraits, Instance
    from traitsui.api import HGroup, UItem, View
    from enable.api import ComponentEditor
    import numpy as np

    x = np.arange(5, 0, -1)
    y = np.arange(5)
    c = np.arange(5)
    s = 10 * (np.arange(5) + 1)

    class Test(HasTraits):
        plot = Instance(OverlayPlotContainer)

        plot2 = Instance(Plot)

        view = View(
            HGroup(
                UItem("plot", editor=ComponentEditor(), style="custom"),
                UItem("plot2", editor=ComponentEditor(), style="custom")
            )
        )

        def _plot_default(self):
            container = OverlayPlotContainer(padding=20)

            plot = create_cmap_scatter_plot([x, y, c, s])
            container.add(plot)
            return container

        def _plot2_default(self):
            data = ArrayPlotData(x=x, y=y, c=c, s=s)
            plot = Plot(data)
            plot.plot(("x", "y", "c"), type="cmap_scatter",
                      color_mapper=jet, marker="circle")
            return plot

    Test().configure_traits()
