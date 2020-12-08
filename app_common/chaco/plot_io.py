import logging
from chaco.api import PlotGraphicsContext

from app_common.pyface.ui.extra_file_dialogs import to_jpg_file_requester, \
    to_png_file_requester

logger = logging.getLogger(__name__)


def save_plot_to_file(plot, filepath=None, width=800, height=600, bgcolor=None,
                      dpi=72, reset=True, file_format=None, pil_options=None):
    """ Save a Chaco Plot or PlotContainer to a file.

    Supported formats include PNG, JPG, BMP, TIFF, EPS.

    WARNING: specifying a jpeg format using 'jpeg' as the extension will lead
    to a failure because of a bug in Kiva. 'jpg' should be used instead.

    Parameters
    ----------
    plot : Plot or PlotContainer
        Plot to print to file.

    filepath : str, optional
        Path to the image file to create. If not specified, a file dialog is
        launched to request it.

    width : int [OPTIONAL]
        Width (outer width to be precise) of the printed plot. Used to reshape
        the provided plot, before rendering the image. Set as None to print
        using current width.

    height : int [OPTIONAL]
        Height (outer height to be precise) of the printed plot. Used to
        reshape the provided plot, before rendering the image. Set as None to
        print using current width.

    bgcolor : str [OPTIONAL]
        Height of the printed plot. Used to reshape the provided plot, before
        rendering the image. Leave empty to use the current background color.

    dpi : int [OPTIONAL, default=72]
        Depth of generated image.

    reset : bool [OPTIONAL, default=True]
        Reset the source plot properties to original state. Only relevant if
        saving with different width, height,
    """

    if file_format is None:
        file_format = "png"

    if filepath is None:
        if file_format == "png":
            filepath = to_png_file_requester()
        elif file_format in ["jpeg", "jpg"]:
            filepath = to_jpg_file_requester()
        else:
            msg = f"Format {file_format} not supported. Please report this " \
                  f"issue and provide the filepath explicitly instead."
            logger.exception(msg)
            raise ValueError(msg)

    if width is None and height is None and bgcolor is None:
        # No reset needed: skip
        reset = False

    if width is None:
        width = plot.outer_width

    if height is None:
        height = plot.outer_height

    old_outer_bounds = [plot.outer_width, plot.outer_height]
    if old_outer_bounds != [width, height]:
        plot.outer_bounds = [width, height]

    if bgcolor:
        old_bgcolor = plot.bgcolor
        plot.bgcolor = bgcolor

    plot.do_layout(force=True)
    try:
        gc = PlotGraphicsContext((width, height), dpi=dpi)
        gc.render_component(plot)
        gc.save(filepath, file_format=file_format, pil_options=pil_options)
    finally:
        if reset:
            if bgcolor:
                plot.bgcolor = old_bgcolor

            plot.outer_bounds = old_outer_bounds
            plot.do_layout(force=True)
