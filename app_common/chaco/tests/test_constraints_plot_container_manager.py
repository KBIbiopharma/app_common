from unittest import TestCase

from chaco.api import Plot
from app_common.chaco.constraints_plot_container_manager import \
    ConstraintsPlotContainerManager


class TestConstraintsPlotContainerManager(TestCase):
    def test_create_empty(self):
        manager = ConstraintsPlotContainerManager()
        self.assertEqual(manager.plot_map, {})
        self.assertIsNone(manager.container)
        manager.init()
        self.assertEqual(manager.container.components, [])

    def test_add_1_plot(self):
        manager = ConstraintsPlotContainerManager()
        manager.init()
        self.assertEqual(manager.container.components, [])
        plot = Plot()
        manager.add_plot("0", plot)
        self.assertEqual(manager.container.components, [plot])

    def test_add_2_plots(self):
        manager = ConstraintsPlotContainerManager()
        manager.init()
        self.assertEqual(manager.container.components, [])
        plot = Plot()
        manager.add_plot("0", plot)
        self.assertEqual(manager.container.components, [plot])
        plot2 = Plot()
        manager.add_plot("foobar", plot2)
        self.assertEqual(manager.container.components, [plot, plot2])

    def test_show_hide_2_plots(self):
        manager = ConstraintsPlotContainerManager()
        manager.init()
        self.assertEqual(manager.container.components, [])
        plot = Plot()
        manager.add_plot("0", plot)
        plot2 = Plot()
        manager.add_plot("foobar", plot2)
        self.assertEqual(manager.container.components, [plot, plot2])
        manager.hide_plot("0")
        self.assertEqual(manager.container.components, [plot2])
        manager.show_plot("0")
        self.assertEqual(manager.container.components, [plot, plot2])
        manager.hide_plot("foobar")
        self.assertEqual(manager.container.components, [plot])
        manager.show_plot("foobar")
        self.assertEqual(manager.container.components, [plot, plot2])

    def test_show_hide_non_existent_plot(self):
        manager = ConstraintsPlotContainerManager()
        manager.init()
        self.assertEqual(manager.container.components, [])
        plot = Plot()
        manager.add_plot("0", plot)
        with self.assertRaises(ValueError):
            manager.hide_plot("NON-EXISTENT")
