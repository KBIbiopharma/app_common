from unittest import TestCase
import numpy as np
from chaco.api import add_default_axes, create_line_plot
from app_common.chaco.overlay_plot_container_utils import align_renderer


class TestAlignRenderer(TestCase):

    def test_align_line_plot(self):
        l1 = [1, 2, 3]
        l2 = [3, 4, 5]
        plot1 = create_line_plot((l1, l2))
        left_axis1, bottom_axis1 = add_default_axes(plot1)
        self.assertEqual(bottom_axis1.mapper.range.low, l1[0])
        self.assertEqual(bottom_axis1.mapper.range.high, l1[-1])

        self.assertEqual(left_axis1.mapper.range.low, l2[0])
        self.assertEqual(left_axis1.mapper.range.high, l2[-1])

        plot2 = create_line_plot((l2, l1))
        left_axis2, bottom_axis2 = add_default_axes(plot2)
        self.assertNotEqual(bottom_axis2.mapper.range.low,
                            bottom_axis1.mapper.range.low)
        self.assertNotEqual(bottom_axis2.mapper.range.high,
                            bottom_axis1.mapper.range.high)

        self.assertNotEqual(left_axis2.mapper.range.low,
                            left_axis1.mapper.range.low)
        self.assertNotEqual(left_axis2.mapper.range.high,
                            left_axis1.mapper.range.high)

        align_renderer(plot2, bottom_axis1)

        self.assertEqual(bottom_axis2.mapper.range.low,
                         bottom_axis1.mapper.range.low)
        self.assertEqual(bottom_axis2.mapper.range.high,
                         bottom_axis1.mapper.range.high)

        align_renderer(plot2, left_axis1, dim="value")

        self.assertEqual(left_axis2.mapper.range.low,
                         left_axis1.mapper.range.low)
        self.assertEqual(left_axis2.mapper.range.high,
                         left_axis1.mapper.range.high)
