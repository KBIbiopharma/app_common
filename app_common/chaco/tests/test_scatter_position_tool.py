from unittest import skipIf, TestCase
import numpy as np
import os
import pandas as pd

try:
    from chaco.api import ArrayPlotData, Plot

    from app_common.chaco.scatter_position_tool import add_scatter_inspectors,\
        DataframeScatterInspector
except ImportError:
    pass

NO_UI_BACKEND = os.environ.get("ETS_TOOLKIT", "qt4") == "null"


@skipIf(NO_UI_BACKEND, "No UI backend")
class TestScatterPositionTool(TestCase):
    def setUp(self):
        num_points = 10
        self.x = np.arange(num_points)
        self.y = np.arange(num_points)
        self.df = pd.DataFrame({"x": self.x, "y": self.y})
        self.plot_data = ArrayPlotData(x=self.x, y=self.y)
        self.plot = Plot(self.plot_data)

    def test_add_tool_to_scatter(self):
        renderer = self.plot.plot(("x", "y"), type="scatter")[0]
        add_scatter_inspectors(self.plot, include_overlay=False)
        self.assertEqual(len(self.plot.tools), 0)
        self.assertEqual(len(renderer.tools), 1)
        scatter_tool = renderer.tools[0]
        self.assertIsInstance(scatter_tool, DataframeScatterInspector)
        # Default plot has a title and a legend, both overlays
        self.assertEqual(len(self.plot.overlays), 2)

    def test_add_tool_to_multiple_scatter(self):
        renderer1 = self.plot.plot(("x", "y"), type="scatter")[0]
        renderer2 = self.plot.plot(("y", "x"), type="scatter")[0]
        add_scatter_inspectors(self.plot, datasets=[self.df, self.df],
                               include_overlay=False)
        self.assertEqual(len(self.plot.tools), 0)
        self.assertEqual(len(renderer1.tools), 1)
        self.assertEqual(len(renderer2.tools), 1)
        scatter_tool = renderer1.tools[0]
        self.assertIsInstance(scatter_tool, DataframeScatterInspector)
        scatter_tool = renderer2.tools[0]
        self.assertIsInstance(scatter_tool, DataframeScatterInspector)

        # Default plot has a title and a legend, both overlays
        self.assertEqual(len(self.plot.overlays), 2)
