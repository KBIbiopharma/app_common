from unittest import skipIf, TestCase
import numpy as np
import os
import pandas as pd
from traits.testing.unittest_tools import UnittestTools
from enable.testing import EnableTestAssistant

try:
    from chaco.api import ArrayPlotData, Plot

    from app_common.chaco.scatter_position_tool import add_scatter_inspectors,\
        DataframeScatterInspector, DataframeScatterOverlay
except ImportError:
    pass

NO_UI_BACKEND = os.environ.get("ETS_TOOLKIT", "qt4") == "null"


@skipIf(NO_UI_BACKEND, "No UI backend")
class TestScatterPositionTool(TestCase, UnittestTools, EnableTestAssistant):
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

    def test_add_tool_to_scatter_with_overlay(self):
        renderer = self.plot.plot(("x", "y"), type="scatter")[0]
        add_scatter_inspectors(self.plot, include_overlay=True)
        self.assertEqual(len(self.plot.tools), 0)
        self.assertEqual(len(renderer.tools), 1)
        scatter_tool = renderer.tools[0]
        self.assertIsInstance(scatter_tool, DataframeScatterInspector)
        # Default plot has a title and a legend, both overlays
        self.assertEqual(len(self.plot.overlays), 3)

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

    def test_add_tool_to_plot_component_as_positional_arg(self):
        """ Make sure we can build the overlay passing component as pos. arg.
        """
        renderer = self.plot.plot(("x", "y"), type="scatter")[0]
        inspector = DataframeScatterInspector(data=self.df, component=renderer)
        renderer.tools.append(inspector)
        overlay = DataframeScatterOverlay(component=self.plot,
                                          inspectors=inspector)
        self.plot.overlays.append(overlay)
        self.assertEqual(overlay.inspectors, [inspector])

    def test_add_tool_to_plot_manually_inspectors_as_obj(self):
        """ Make sure we can build the overlay passing a single inspector."""
        renderer = self.plot.plot(("x", "y"), type="scatter")[0]
        inspector = DataframeScatterInspector(data=self.df, component=renderer)
        renderer.tools.append(inspector)
        overlay = DataframeScatterOverlay(component=self.plot,
                                          inspectors=inspector)
        self.plot.overlays.append(overlay)

        self.assertEqual(overlay.inspectors, [inspector])

    def test_add_tool_to_plot_manually(self):
        renderer = self.plot.plot(("x", "y"), type="scatter")[0]
        inspector = DataframeScatterInspector(data=self.df, component=renderer)
        renderer.tools.append(inspector)
        overlay = DataframeScatterOverlay(component=self.plot,
                                          inspectors=[inspector])
        self.plot.overlays.append(overlay)

        self.assertEqual(overlay.text, "")
        with self.assertTraitChanges(inspector, "inspector_event"):
            with self.assertTraitChanges(overlay, "text"):
                x, y = self.plot.map_screen(data_array=[self.x[0], self.y[0]])
                self.mouse_move(inspector, x=x, y=y)

            self.assertEqual(overlay.text, "x: 0\ny: 0")

    def test_add_tool_to_plot_manually_control_single_formatting(self):
        renderer = self.plot.plot(("x", "y"), type="scatter")[0]
        inspector = DataframeScatterInspector(data=self.df, component=renderer)
        renderer.tools.append(inspector)
        overlay = DataframeScatterOverlay(component=self.plot,
                                          inspectors=[inspector],
                                          val_fmts=":.2f")
        self.plot.overlays.append(overlay)

        self.assertEqual(overlay.text, "")
        with self.assertTraitChanges(inspector, "inspector_event"):
            with self.assertTraitChanges(overlay, "text"):
                x, y = self.plot.map_screen(data_array=[self.x[0], self.y[0]])
                self.mouse_move(inspector, x=x, y=y)

            self.assertEqual(overlay.text, "x: 0.00\ny: 0.00")

    def test_add_tool_to_plot_manually_control_custom_formatting(self):
        renderer = self.plot.plot(("x", "y"), type="scatter")[0]
        inspector = DataframeScatterInspector(data=self.df, component=renderer)
        renderer.tools.append(inspector)
        overlay = DataframeScatterOverlay(component=self.plot,
                                          inspectors=[inspector],
                                          val_fmts={"y": ":.2f"})
        self.plot.overlays.append(overlay)

        self.assertEqual(overlay.text, "")
        with self.assertTraitChanges(inspector, "inspector_event"):
            with self.assertTraitChanges(overlay, "text"):
                x, y = self.plot.map_screen(data_array=[self.x[0], self.y[0]])
                self.mouse_move(inspector, x=x, y=y)

            self.assertEqual(overlay.text, "x: 0\ny: 0.00")

    def test_add_tool_to_plot_manually_control_custom_message(self):
        renderer = self.plot.plot(("x", "y"), type="scatter")[0]
        inspector = DataframeScatterInspector(data=self.df, component=renderer)
        renderer.tools.append(inspector)
        overlay = DataframeScatterOverlay(
            component=self.plot,
            inspectors=[inspector],
            message_for_data=lambda inspector, data_idx: "foobar"
        )
        self.plot.overlays.append(overlay)

        self.assertEqual(overlay.text, "")
        with self.assertTraitChanges(inspector, "inspector_event"):
            with self.assertTraitChanges(overlay, "text"):
                x, y = self.plot.map_screen(data_array=[self.x[0], self.y[0]])
                self.mouse_move(inspector, x=x, y=y)

            self.assertEqual(overlay.text, "foobar")
