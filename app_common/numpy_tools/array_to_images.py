""" Utilities to write numpy arrays to image files.
"""
import logging
from os.path import splitext

from numpy import min, max
from scipy.misc import toimage


logger = logging.getLogger(__name__)


def write_array_to_image(img_array, filepath, writer_func=None, **kwargs):
    """ API interface function to store a particle image array (2D) to a file.

    Supported file formats include PNG, JPEG, HDF5. Use specific writer
    """
    if writer_func is None:
        ext = splitext(filepath)[1].lower()
        writers = {".png": write_array_to_png_image,
                   ".jpeg": write_array_to_jpeg_image,
                   ".jpg": write_array_to_jpeg_image,
                   ".hdf5": write_array_to_h5_file,
                   ".h5": write_array_to_h5_file}
        writer_func = writers[ext]

    result = writer_func(img_array, filepath, **kwargs)

    if result:
        logger.debug("Array written to {}".format(filepath))


def write_array_to_jpeg_image(img_array, filepath, mode=None):
    """ Dump a numpy array to a JPEG file (LOSSY!).

    Parameters
    ----------
    img_array : ndarray
        Numpy array to serialize.

    filepath : str
        Path to the image file to create.

    mode : str
        Mode for the conversion to PIL.Image. Leave as None for uint8 arrays.
        Requesting it as an argument to avoid an if statement for situation
        where MANY files must be created from arrays with the same dtype.
    """
    # Create a PIL image and then save:
    img = toimage(img_array, low=min(img_array), high=max(img_array),
                  mode=mode)
    img.save(filepath)
    return True


def write_array_to_png_image(img_array, filepath, mode=None):
    """ Dump an numpy array to a PNG file (LOSSLESS if uint8/uint16 dtype!).

    Parameters
    ----------
    img_array : ndarray
        Numpy array to serialize. dtype must be uint8/uint16.

    filepath : str
        Path to the image file to create.

    mode : str
        Mode for the conversion to PIL.Image. Leave as None for uint8 arrays.
        Set to 'I' to create 16bit PNG file (to remain lossless for uint16
        arrays). Requesting it as an argument to avoid an if statement for
        situation where MANY files must be created from arrays with the same
        dtype.
    """
    # Create a PIL image and then save:
    img = toimage(img_array, low=min(img_array), high=max(img_array),
                  mode=mode)
    img.save(filepath)
    return True


def write_array_to_h5_file(img_array, filepath, node, node_shape=None,
                           slice_start=None, slice_end=None):
    """ Dump a numpy array of integers to a JPEG file.

    Parameters
    ----------
    img_array : ndarray
        Numpy array to serialize. dtype must be integer.

    filepath : str
        Path to the image file to create.

    FIXME: add tests and support for compression.
    """
    from h5py import File

    with File(filepath, "a") as h5file:
        if node not in h5file.nodes:
            dset = h5file.create_dataset(node, node_shape, dtype='i')
        else:
            dset = h5file.get(node)

        dset[slice_start:slice_end] = img_array
    return True
