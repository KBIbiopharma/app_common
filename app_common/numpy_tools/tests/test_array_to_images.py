from unittest import TestCase
import numpy as np
from numpy.testing import assert_array_equal
import os

from app_common.numpy_tools.array_to_images import write_array_to_image
from scipy.misc import imread


class TestWriteParticleImage(TestCase):
    def setUp(self):
        self.array8 = np.array([[1, 2, 1, 4, 6, 34],
                                [63, 1, 200, 1, 45, 1],
                                [1, 2, 3, 4, 0, 0],
                                [1, 12, 11, 21, 31, 35]], dtype="uint8")

        self.array16 = np.array([[21, 12, 1, 4, 6, 34],
                                 [63, 1, 2000, 1, 45, 1],
                                 [10, 2, 3, 214, 0, 0],
                                 [1, 20, 11, 221, 31, 35]], dtype="uint16")

    def test_write_read_png_uint8(self):
        fname = "test.png"
        if os.path.isfile(fname):
            os.remove(fname)

        try:
            write_array_to_image(self.array8, fname)
            self.assertIn(fname, os.listdir("."))
            a_out = imread(fname)
            assert_array_equal(a_out, self.array8)
        finally:
            if os.path.isfile(fname):
                os.remove(fname)

    def test_write_read_png_uint16(self):
        fname = "test.png"
        if os.path.isfile(fname):
            os.remove(fname)

        try:
            write_array_to_image(self.array16, fname, mode="I")
            a_out = imread(fname)
            assert_array_equal(a_out, self.array16)
        finally:
            if os.path.isfile(fname):
                os.remove(fname)

    def test_fail_write_read_png_uint16(self):
        # Fails because by default writes a 8-bit PNG file:
        with self.assertRaises(ValueError):
            write_array_to_image(self.array16, "test.png")

    def test_write_read_jpeg_uint8(self):
        fname = "test.jpeg"
        if os.path.isfile(fname):
            os.remove(fname)

        try:
            write_array_to_image(self.array8, fname)
            self.assertIn(fname, os.listdir("."))
            a_out = imread(fname)
            # JPEG is lossy, so just make sure the shape is the same
            self.assertEqual(a_out.shape, self.array8.shape)
        finally:
            if os.path.isfile(fname):
                os.remove(fname)
