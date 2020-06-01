""" Extended renderer factories.

Remove when https://github.com/enthought/chaco/pull/514 is merged and in use.
"""
from numpy import array, ndarray
from chaco.api import AbstractDataSource, ArrayDataSource, \
    ColormappedScatterPlot, ColorMapper, DataRange1D, jet, LinearMapper, LogMapper
from chaco.plot_factory import add_default_grids, add_default_axes
from chaco.color_mapper import ColorMapper



def create_line_plot(**kwargs):
    from chaco.plot_factory import create_line_plot

    alpha = kwargs.pop("alpha")
    renderer = create_line_plot(**kwargs)
    renderer.alpha = alpha
    return renderer


def create_scatter_plot(**kwargs):
    from chaco.plot_factory import create_scatter_plot

    alpha = kwargs.pop("alpha")
    renderer = create_scatter_plot(**kwargs)
    renderer.alpha = alpha
    return renderer


def create_bar_plot(**kwargs):
    from chaco.plot_factory import create_bar_plot

    alpha = kwargs.pop("alpha")
    renderer = create_bar_plot(**kwargs)
    renderer.alpha = alpha
    return renderer


def create_cmap_scatter_plot(data=None, index_bounds=None, value_bounds=None,
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
    if len(data) > 4 or len(data) < 3:
        msg = "Colormapped segment plots require (index, value, color) or " \
              "(index, value, color, width) data"
        raise ValueError(msg)

    elif len(data) == 3:
        index, value, color_data = _create_data_sources(data)

    elif len(data) == 4:
        index, value, color_data, size = _create_data_sources(data)

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
    index_mapper = LinearMapper(range=index_range)

    if value_bounds is not None:
        value_range = DataRange1D(low=value_bounds[0], high=value_bounds[1])
    else:
        value_range = DataRange1D()
    value_range.add(value)
    value_mapper = LinearMapper(range=value_range)

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
                                  marker_size=size,
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
    from chaco.api import OverlayPlotContainer
    from traits.api import HasTraits, Instance
    from traitsui.api import UItem, View
    from enable.api import ComponentEditor
    import numpy as np


    class Test(HasTraits):
        plot = Instance(OverlayPlotContainer)

        view = View(
            UItem("plot", editor=ComponentEditor(), style="custom")
        )

        def _plot_default(self):
            container = OverlayPlotContainer(padding=20)
            x = np.random.randn(20)
            y = np.random.randn(20)
            c = np.random.randn(20)
            s = 10 * np.random.randn(20)
            plot = create_cmap_scatter_plot([x, y, c, s])
            container.add(plot)
            return container

    Test().configure_traits()
