from unittest import TestCase
import numpy as np

from chaco.api import BarPlot, ColormappedScatterPlot, ImagePlot, LinePlot, \
    ScatterPlot, ContourLinePlot
from app_common.chaco.plot_factory import create_bar_plot, \
    create_contour_plot, create_cmap_scatter_plot, create_img_plot, \
    create_line_plot, create_scatter_plot
from app_common.apptools.testing_utils import assert_obj_gui_works


class BaseRendererMakers(object):
    def test_create_default_renderer(self):
        rend = self.factory(data=self.data)
        self.assertIsInstance(rend, self.rend_type)

    def test_embed_renderer_and_view(self):
        rend = self.factory(data=self.data)
        traits_view = embed_renderer_in_traits(rend)
        assert_obj_gui_works(traits_view)


class TestCreateLinePlot(BaseRendererMakers, TestCase):
    def setUp(self):
        self.factory = create_line_plot
        self.rend_type = LinePlot
        self.data = [(1, 2, 3), (1, 2, 3)]


class TestCreateBarPlot(BaseRendererMakers, TestCase):
    def setUp(self):
        self.factory = create_bar_plot
        self.rend_type = BarPlot
        self.data = [(1, 2, 3), (1, 2, 3)]


class TestCreateScatterPlot(BaseRendererMakers, TestCase):
    def setUp(self):
        self.factory = create_scatter_plot
        self.rend_type = ScatterPlot
        self.data = [(1, 2, 3), (1, 2, 3)]


class TestCreateCmapScatterPlot(BaseRendererMakers, TestCase):
    def setUp(self):
        self.factory = create_cmap_scatter_plot
        self.rend_type = ColormappedScatterPlot
        self.data = [(1, 2, 3), (1, 2, 3), (1, 2, 3)]


class TestCreateImgPlot(BaseRendererMakers, TestCase):
    def setUp(self):
        self.factory = create_img_plot
        self.rend_type = ImagePlot
        self.data = np.array([(1, 2, 3), (1, 2, 3), (1, 2, 3)])


class TestCreateContourPlot(BaseRendererMakers, TestCase):
    def setUp(self):
        self.factory = create_contour_plot
        self.rend_type = ContourLinePlot
        self.data = np.array([(1, 2, 3), (1, 2, 3), (1, 2, 3)])


def embed_renderer_in_traits(rend):
    from chaco.api import OverlayPlotContainer, Plot
    from traits.api import HasTraits, Instance
    from traitsui.api import HGroup, UItem, View
    from enable.api import ComponentEditor

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
            container.add(rend)
            return container

    return Test()
