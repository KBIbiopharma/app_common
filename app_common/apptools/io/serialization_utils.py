""" Utilities for implementing serialization of Traits objects.
"""

from tables import open_file
import uuid
import getpass
import datetime
import zipfile
import os
from os.path import abspath, basename, isfile, join, splitext
import json
import logging
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_PANDAS_HDF5_FILENAME = 'pandas_file.h5'

DEFAULT_ARR_HDF5_FILENAME = 'ndarray_file.h5'


def get_object_id(_object):
    return id(_object)


def get_ndArray_id(ndArray):
    """ Build a unique random ID for an array which follows natural naming
    (meaning following the pattern `^[a-zA-Z_][a-zA-Z0-9_]*$`). That allows
    pytables to support exploring objects with tab completion since the
    resulting string is a valid variable name.
    """
    return "id_" + str(uuid.uuid4()).replace("-", "_")


def get_save_timestamp():
    return str(datetime.datetime.now())


def get_user():
    return getpass.getuser()


def get_data_filename(obj):
    """ Select the filename to store the object passed.
    """
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        return DEFAULT_PANDAS_HDF5_FILENAME
    else:
        return DEFAULT_ARR_HDF5_FILENAME


def write_ndArray_to_hdf5(array_collection, target_dir="."):
    """ Write all ndarrays to specified folder as specified in data_collection.

    Parameters
    ----------
    target_dir : str (Optional)
        Path to an exiting directory to create the files into. By default,
        creating the file where the interpreter is launched.

    array_collection : dict
        Dict mapping the HDF5 filenane and path within the file to store the
        array into.

    Returns
    -------
    List of all file paths arrays were written to.
    """
    file_handles = {}

    for (filename, obj_id), obj in array_collection.items():
        obj_id = str(obj_id)
        file_path = join(target_dir, filename)

        if file_path not in file_handles:
            if filename == DEFAULT_ARR_HDF5_FILENAME:
                file_handles[file_path] = open_file(file_path, mode="a")
            else:
                file_handles[file_path] = pd.HDFStore(file_path, mode="a")

        fileh = file_handles[file_path]
        if isinstance(obj, (pd.DataFrame, pd.Series)):
            fileh[obj_id] = obj
        else:
            fileh.create_array("/",  obj_id, obj)

    for file_handle in file_handles.values():
        file_handle.close()
    return file_handles.keys()


def write_serialized_data_to_json(file_path, serialized_data, overwrite=False):
    """ Write all json-dumpable data to specified json file.

    Parameters
    ----------
    file_path : str
        Path to the (json) file to store all serial data.

    serialized_data : dict
        Dict containing the serialized data to write to file, as returned by
        an implemented serialize function.
    """
    if isfile(file_path) and not overwrite:
        msg = ("File {} already exists. Set overwrite to True to ignore "
               "existing files.".format(file_path))
        logger.exception(msg)
        raise IOError(msg)

    with open(file_path, 'w') as fp:
        json.dump(serialized_data, fp, indent=2)

    logger.debug("Stored json data in {}".format(file_path))
    return file_path


def read_ndArray_from_hdf5(filenames):
    """ Read all Arrays found in the provided files.

    Parameters
    ----------
    filenames : list
        List of HDF5 files to search for arrays into.

    Returns
    -------
    A dictionary of numpy arrays and pandas objects, mapped to their file and
    path.
    """
    data_dict = {}
    for filename in filenames:
        with open_file(filename, "r") as h5file:
            for node in h5file.walk_nodes("/", "Array"):
                array = node.read()
                key = (os.path.basename(filename), node.name)
                data_dict[key] = array

            # Now listing groups because a dataframe or a series is stored as a
            # group directly inside the root node:
            group_names = h5file.root._g_list_group(h5file.root)[0]
            group_keys = [(basename(filename), group) for group in group_names]

        with pd.HDFStore(filename, "r") as store:
            for key in group_keys:
                data_dict[key] = store.get(key[1])

    return data_dict


def zip_files(target_filepath, file_list):
    """ Create zip file which includes all files in the specified list.

    If the filepaths in the file_list contain folders, these get ignored in the
    target zipfile.

    Warning: if the target path exists, the file will be overwritten.

    Parameters
    ----------
    target_filepath : str
        Path including name of the target zip file.

    file_list : list
        List of files to zip.
    """
    # Support very large files with allowZip64:
    zf = zipfile.ZipFile(target_filepath, mode='w', allowZip64=True)
    for file_to_zip in file_list:
        target_filename = basename(file_to_zip)
        zf.write(file_to_zip, arcname=target_filename)
    zf.close()
    return


def unzip_files(zipped_file, target_folder=""):
    """ Create zip file which includes all files in the specified list.

    Warning: if the target path exists, the file will be overwritten.

    Parameters
    ----------
    zipped_file : str
        Path to the zip file to unzip

    target_folder : str
        Target folder to create to contain the content of the zip file.

    Returns
    """
    file_list = []
    zf = zipfile.ZipFile(zipped_file, 'r')
    if not target_folder:
        target_folder = splitext(abspath(zipped_file))[0]

    zf.extractall(target_folder)
    for filename in zf.namelist():
        file_list.append(join(target_folder, filename))
    return file_list


def read_serialized_data_from_files(file_list):
    """ Read all data from an unzipped project file.

    Parameters
    ----------
    file_list : list
        List of files extracted from a project file unzipped.
    """
    hdf5_files = [filename for filename in file_list if
                  splitext(filename)[1] == '.h5']

    array_collection = read_ndArray_from_hdf5(hdf5_files)

    json_files = [filename for filename in file_list if
                  splitext(filename)[1] == '.json']

    if not len(json_files) == 1:
        msg = "More than 1 json file found: {}".format(file_list)
        logger.exception(msg)
        raise NotImplementedError(msg)

    with open(json_files[0]) as json_file:
        json_data = json.load(json_file)
    return json_data, array_collection


def sanitize_class_name(class_name):
    """ Make sure the first letter is uncapatalized to match the class name
    of the deserializer
    """
    class_name = class_name[0].lower() + class_name[1:]
    return class_name
