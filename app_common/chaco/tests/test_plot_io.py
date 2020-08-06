from unittest import TestCase, skipIf
import os
from imageio import imread

try:
    from chaco.api import ArrayPlotData, GridPlotContainer, Plot
    from app_common.chaco.plot_io import save_plot_to_file
    skip = False
except ImportError:
    skip = True


class BasePlotSave(object):
    def setUp(self):
        self.filename = "unittest_TestChacoPlotSave.png"
        self.target_files = {self.filename}

    def tearDown(self):
        for fname in self.target_files:
            if os.path.isfile(fname):
                os.remove(fname)

    def test_save_single_plot(self):
        base_filename = "unittest_TestChacoPlotSave."
        for ext in ["png", "jpg", "bmp"]:
            filename = base_filename + ext
            self.target_files.add(filename)
            save_plot_to_file(self.plot, filename)
            self.assertIn(filename, os.listdir("."))
            self.assert_image_not_all_white(filename)

    def test_save_with_new_shape(self):
        filename = self.filename
        self.plot.width = 600
        self.plot.height = 600
        save_plot_to_file(self.plot, filename, width=1000, height=1000)
        self.assertIn(filename, os.listdir("."))
        # Make sure that the source plot is reset to its original size:
        self.assertEqual(self.plot.width, 600)
        self.assertEqual(self.plot.height, 600)

    def test_save_with_new_bgcolor(self):
        filename = self.filename
        self.plot.bgcolor = "lightgray"
        save_plot_to_file(self.plot, filename, bgcolor="white")
        self.assertIn(filename, os.listdir("."))
        # Make sure that the source plot is reset to its original bgcolor:
        self.assertEqual(self.plot.bgcolor, "lightgray")

    def test_save_with_new_bgcolor_and_shape(self):
        filename = self.filename
        self.plot.bgcolor = "lightgray"
        self.plot.width = 600
        self.plot.height = 600
        save_plot_to_file(self.plot, filename, width=1000, height=1000,
                          bgcolor="white")
        self.assertIn(filename, os.listdir("."))
        # Make sure that the source plot is reset to its original bgcolor and
        # size:
        self.assertEqual(self.plot.width, 600)
        self.assertEqual(self.plot.height, 600)
        self.assertEqual(self.plot.bgcolor, "lightgray")

    def test_save_to_jpg_twice(self):
        filename = self.filename
        save_plot_to_file(self.plot, filename)

        plot2 = Plot(self.data)
        plot2.plot(("x", "y"))
        filename2 = "unittest_TestChacoPlotSave2.jpg"
        self.target_files.add(filename2)
        save_plot_to_file(plot2, filename2)
        self.assert_image_not_all_white(filename)
        self.assert_image_not_all_white(filename2)

    # Assertion methods -------------------------------------------------------

    def assert_image_not_all_white(self, filepath):
        img_data = imread(filepath)
        self.assertFalse((img_data == 255).all())


@skipIf(skip, "No backend available")
class TestPlotSave(BasePlotSave, TestCase):
    def setUp(self):
        super(TestPlotSave, self).setUp()

        self.data = ArrayPlotData(x=[1, 2, 3], y=[1, 2, 3])
        self.plot = Plot(self.data)
        self.plot.plot(("x", "y"))


@skipIf(skip, "No backend available")
class TestPlotContainerSave(BasePlotSave, TestCase):
    def setUp(self):
        super(TestPlotContainerSave, self).setUp()

        self.data = ArrayPlotData(x=[1, 2, 3], y=[1, 2, 3])
        plot = Plot(self.data)
        plot.plot(("x", "y"))

        self.plot = GridPlotContainer(shape=(1, 1))
        self.plot.add(plot)
