from unittest import TestCase
import numpy as np

from chaco.api import BarPlot, ColormappedScatterPlot, GridMapper, ImagePlot, \
    LogMapper, LinePlot, ScatterPlot, ContourLinePlot
from app_common.chaco.plot_factory import create_bar_plot, \
    create_contour_plot, create_cmap_scatter_plot, create_img_plot, \
    create_line_plot, create_scatter_plot
from app_common.chaco.testing_utils import embed_renderer_in_traits
from app_common.apptools.testing_utils import assert_obj_gui_works


class BaseRendererMakers(object):
    def test_create_default_renderer(self):
        rend = self.factory(data=self.data)
        self.assertIsInstance(rend, self.rend_type)

    def test_create_renderer_with_alpha(self):
        rend = self.factory(data=self.data, alpha=0.4)
        self.assertIsInstance(rend, self.rend_type)
        self.assertEqual(rend.alpha, 0.4)

    def test_create_x_log_renderer(self):
        rend = self.factory(data=self.data, index_mapper_class=LogMapper)
        self.assertIsInstance(rend, self.rend_type)
        self.assertIsInstance(rend.index_mapper, LogMapper)

    def test_create_y_log_renderer(self):
        rend = self.factory(data=self.data, value_mapper_class=LogMapper)
        self.assertIsInstance(rend, self.rend_type)
        self.assertIsInstance(rend.value_mapper, LogMapper)

    def test_embed_renderer_and_view(self):
        rend = self.factory(data=self.data)
        traits_view = embed_renderer_in_traits(rend)
        assert_obj_gui_works(traits_view)


class Base2DRendererMakers(BaseRendererMakers):
    def test_create_x_log_renderer(self):
        rend = self.factory(data=self.data, index_mapper_class=LogMapper)
        self.assertIsInstance(rend, self.rend_type)
        self.assertIsInstance(rend.index_mapper, GridMapper)
        self.assertIsInstance(rend.index_mapper._xmapper, LogMapper)

    def test_create_y_log_renderer(self):
        rend = self.factory(data=self.data, value_mapper_class=LogMapper)
        self.assertIsInstance(rend, self.rend_type)
        self.assertIsInstance(rend.index_mapper, GridMapper)
        self.assertIsInstance(rend.index_mapper._ymapper, LogMapper)


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


class TestCreateImgPlot(Base2DRendererMakers, TestCase):
    def setUp(self):
        self.factory = create_img_plot
        self.rend_type = ImagePlot
        self.data = np.array([(1, 2, 3), (1, 2, 3), (1, 2, 3)])


class TestCreateContourPlot(Base2DRendererMakers, TestCase):
    def setUp(self):
        self.factory = create_contour_plot
        self.rend_type = ContourLinePlot
        self.data = np.array([(1, 2, 3), (1, 2, 3), (1, 2, 3)])
