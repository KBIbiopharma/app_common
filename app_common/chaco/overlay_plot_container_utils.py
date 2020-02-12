""" Utilities to build flexible overlaid plots using an OverlayPlotContainer.

The goal is to bridge the gap between the ease of use of chaco's Plot and the
flexibility power of the OverlayPlotContainer classes.
"""


def align_renderer(renderer, axis, dim="index"):
    """ Align a renderer's index or value mapper along provided axis.

    The purpose of this function is to align a renderer on an existing PlotAxis
    without the nuclear option of setting the renderer's mapper to the axis
    mapper. Obviously, making the 2 mappers the same object works well to align
    multiple plots with each other.

    But having the same mappers leads to the wrong behavior of the ZoomTool's
    box drawing feature. The only way to make it work is for mappers to remain
    distinct but aligned. This function does that.

    Parameters
    ----------
    renderer : AbstractPlotRenderer
        Renderer to align.

    axis : PlotAxis
        Axis to align the renderer along.

    dim : str
        Dimension along which to align the renderer. Valid values are "index"
        and "value".
    """
    axis.mapper.range.add(getattr(renderer, dim))
    mapper = getattr(renderer, dim + "_mapper")
    mapper.range.low = axis.mapper.range.low
    mapper.range.high = axis.mapper.range.high
