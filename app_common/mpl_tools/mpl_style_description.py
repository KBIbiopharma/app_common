""" Class to gather general Matplotlib style options for various types of
plots, to provide a unified way to collect them and
"""
from matplotlib import cm

from traits.api import Any, Bool, Float, HasStrictTraits, Int, Str


class PltStyleDescription(HasStrictTraits):
    """ General Matplotlib plot styling description.
    """
    #: Whether to draw a grid
    include_grid = Bool(False)

    #: Include a legend?
    include_legend = Bool(True)

    #: Location of the legend
    legend_loc = Str("lower right")

    #: Legend text font size
    legend_fontsize = Int(12)

    #: Font size for the x label and x-ticks
    x_fontsize = Int(14)

    #: Font size for the y label and y-ticks
    y_fontsize = Int(14)

    #: Font size for the title
    title_fontsize = Int(14)

    #: Colormap to use on heatmaps
    colormap = Any(cm.jet)

    #: Whether to add contours to a heatmap
    include_contours = Bool(True)

    #: If contours are added, fontsize of the countour labels:
    contour_fontsize = Int(9)

    #: If contours are added, how many should be generated (at most)
    countour_num = Int(5)

    #: If contours are added, thickness of the contour line
    contour_linewidth = Float(.5)

    def __init__(self, **traits):
        # All fontsizes were specified with a unique 'fontsize' entry. Apply:
        if "fontsize" in traits:
            fontsize = traits.pop("fontsize")
            for attr in ["x_fontsize", "y_fontsize", "title_fontsize"]:
                traits[attr] = fontsize

        super(PltStyleDescription, self).__init__(**traits)
