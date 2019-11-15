import os
import logging
import shutil
from tempfile import mkdtemp

from traits.api import Callable, HasStrictTraits, provides, Str

from .serializer import serialize
from .deserializer import deserialize
from .i_reader_i_writer import IReader, IWriter
from .serialization_utils import write_ndArray_to_hdf5, zip_files, \
    unzip_files, read_serialized_data_from_files, write_serialized_data_to_json

logger = logging.getLogger(__name__)

DEFAULT_JSON_FILENAME = "temp_json_file.json"


def save_object(filepath, object_to_save):
    """ Stores any Traits object into a file.

    Parameters
    ----------
    filepath : str
        Absolute or relative path to the file to load.

    object_to_save : any
        Object to save. It is expected to be a subclass of HasTraits.
    """
    writer = LocalFileWriter(filepath=filepath, serialize=serialize)
    writer.save(object_to_save)


def load_object(filepath):
    """ Load Traits object from file.

    Parameters
    ----------
    filepath : str
        Absolute or relative path to the file to load.

    Returns
    -------
    any, bool
        The object found in the file and a flag set to True if the file
        required legacy deserializers to be be read.
    """
    reader = LocalFileReader(filepath=filepath, deserialize=deserialize)
    return reader.load()


@provides(IWriter)
class LocalFileWriter(HasStrictTraits):
    """ Writer to store a HasTraits object to a local filesystem file.

    Examples
    --------
    >>> writer = LocalFileWriter(filepath=filepath)
    >>> writer.save(object_to_save)
    """
    #: File path to write to
    filepath = Str

    #: API function to serialize objects using the appropriate Serializer attrs
    serialize = Callable

    def save(self, object_to_save):
        t = type(object_to_save)
        msg = 'Saving {} to file {}.'.format(t, self.filepath)
        logger.debug(msg)

        serial_data, array_collection = self.serialize(object_to_save)

        target_dir = mkdtemp()
        files_to_save = []
        try:
            filename = os.path.join(target_dir, DEFAULT_JSON_FILENAME)
            json_filename = write_serialized_data_to_json(filename,
                                                          serial_data)
            files_to_save.append(json_filename)

            hdf5_filenames = write_ndArray_to_hdf5(array_collection,
                                                   target_dir)
            files_to_save += hdf5_filenames
            zip_files(self.filepath, files_to_save)
        except Exception as e:
            msg = "Failed to store object to {}. Error was {}"
            msg = msg.format(self.filepath, e)
            logger.exception(msg)
            raise IOError(msg)
        else:
            logger.debug('Object saved in {}.'.format(self.filepath))
        finally:
            shutil.rmtree(target_dir)


@provides(IReader)
class LocalFileReader(HasStrictTraits):
    """ Reader to load a Chromatography object from a local filesystem file.

    Examples
    --------
    >>> reader = LocalFileReader(filepath=filepath)
    >>> object_stored = reader.load()
    ...
    """
    #: File path to read from
    filepath = Str

    #: API function to deserialize objects using appropriate DeSerializer attrs
    deserialize = Callable

    def load(self):
        logger.debug('Loading from {}'.format(self.filepath))
        filepath = self.filepath
        target_folder = mkdtemp()
        file_list = []
        try:
            file_list = unzip_files(filepath, target_folder=target_folder)
            json_data, array_collection = read_serialized_data_from_files(
                file_list
            )
            obj, legacy = self.deserialize(json_data,
                                           array_collection=array_collection)
        except Exception as e:
            msg = "Failed to load {}. Error was {}".format(filepath, e)
            logger.exception(msg)
            raise IOError(msg)
        else:
            logger.debug('Object loaded!')
        finally:
            for filepath in file_list:
                os.remove(filepath)
            shutil.rmtree(target_folder)
        return obj, legacy
