from unittest import TestCase, skipIf
import numpy as np
import os

try:
    from chaco.api import ArrayPlotData, Plot
    from app_common.chaco.mouse_position_tool import add_mouse_position_tool, \
        MousePositionTool, MousePositionOverlay
except ImportError:
    pass

NO_UI_BACKEND = os.environ.get("ETS_TOOLKIT", "qt4") == "null"


@skipIf(NO_UI_BACKEND, "No UI backend")
class TestMousePositionTool(TestCase):
    def setUp(self):
        num_points = 10
        self.x = np.arange(num_points)
        self.y = np.arange(num_points)
        self.plot_data = ArrayPlotData(x=self.x, y=self.y)
        self.plot = Plot(self.plot_data)

    def test_add_tool_to_scatter(self):
        self.plot.plot(("x", "y"), type="scatter")
        add_mouse_position_tool(self.plot, include_overlay=False)
        self.assertEqual(len(self.plot.tools), 1)
        mouse_tool = self.plot.tools[0]
        self.assertIsInstance(mouse_tool, MousePositionTool)
        # Default plot has a title and a legend, both overlays
        self.assertEqual(len(self.plot.overlays), 2)

    def test_add_tool_and_overlay_to_scatter(self):
        self.plot.plot(("x", "y"), type="scatter")
        add_mouse_position_tool(self.plot, include_overlay=True)
        self.assertEqual(len(self.plot.tools), 1)
        mouse_tool = self.plot.tools[0]
        self.assertIsInstance(mouse_tool, MousePositionTool)

        # Default plot has a title and a legend, both overlays
        self.assertEqual(len(self.plot.overlays), 3)
        mouse_overlay = self.plot.overlays[-1]
        self.assertIsInstance(mouse_overlay, MousePositionOverlay)

    def test_add_tool_to_line(self):
        self.plot.plot(("x", "y"))
        add_mouse_position_tool(self.plot, include_overlay=False)
        self.assertEqual(len(self.plot.tools), 1)
        mouse_tool = self.plot.tools[0]
        self.assertIsInstance(mouse_tool, MousePositionTool)
        # Default plot has a title and a legend, both overlays
        self.assertEqual(len(self.plot.overlays), 2)

    def test_add_tool_and_overlay_to_line(self):
        self.plot.plot(("x", "y"))
        add_mouse_position_tool(self.plot, include_overlay=True)
        self.assertEqual(len(self.plot.tools), 1)
        mouse_tool = self.plot.tools[0]
        self.assertIsInstance(mouse_tool, MousePositionTool)

        # Default plot has a title and a legend, both overlays
        self.assertEqual(len(self.plot.overlays), 3)
        mouse_overlay = self.plot.overlays[-1]
        self.assertIsInstance(mouse_overlay, MousePositionOverlay)
