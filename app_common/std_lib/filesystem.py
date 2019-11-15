import logging
import re
import os
from os.path import getsize, isdir, join
from functools import partial

logger = logging.getLogger(__name__)

BYTE_UNIT_FACTORS = {"B": 1., "KB": 1.e-3, "MB": 1.e-6, "GB": 1.e-9}


def get_dir_size(target_dir, unit="MB", details=False, verbose=0, exclude=""):
    """ Compute the total folder size by recursively walking its content and
    summing the size of all files found.

    Parameters
    ----------
    target_dir : str
        Path to the folder to analyze.

    unit : str [OPTIONAL, default="MB"]
        Unit in which to compute the sizes. Valid values are 'B', 'KB', 'MB'
        and 'GB'.

    details : bool [OPTIONAL]
        Whether to count the number of files in each subdirectory too.

    verbose : int [OPTIONAL, default=0]
        Whether to print results along the way. Only applicable if details is
        True. Display count along the way if set to 1. Display file names along
        the way if set to 2.

    exclude : str [OPTIONAL]
        Regex pattern of file *name* to exclude from the count.

    Returns
    -------
    int [dict]
        Total file size, and optionally a dictionary of subdirectories
        and their number of files, if details=True.
    """
    init_size = 0.
    detail_data = {}
    if not isdir(target_dir):
        msg = "Target folder doesn't exist."
        logger.exception(msg)
        raise ValueError(msg)

    msg = "Computing size of {}..."
    logger.debug(msg.format(target_dir))
    unit_factor = BYTE_UNIT_FACTORS[unit]
    for dirpath, dirnames, filenames in os.walk(target_dir):
        if exclude:
            path_size = sum(getsize(join(dirpath, name)) for name in filenames
                            if not re.match(exclude, name))
        else:
            path_size = sum(getsize(join(dirpath, name)) for name in filenames)

        path_size *= unit_factor
        if details:
            rel_dirpath = dirpath.replace(target_dir, "")
            detail_data[rel_dirpath] = path_size
            if verbose:
                print("{} {} found in {}".format(path_size, unit, rel_dirpath))
                if verbose > 1:
                    msg = "Following files found in {}: {}".format(rel_dirpath,
                                                                   filenames)
                    print(msg)

        init_size += path_size

    if details:
        return init_size, detail_data
    else:
        return init_size


def get_dir_file_count(target_dir, details=False, verbose=0, exclude=""):
    """ Count the number of files in a folder and optionally its sub-folders.

    Parameters
    ----------
    target_dir : str
        Path to the folder to analyze.

    details : bool [OPTIONAL, default=False]
        Whether to count the number of files in each subdirectory too.

    verbose : int [OPTIONAL, default=0]
        Whether to print results along the way. Only applicable if details is
        True. Display count along the way if set to 1. Display filenames along
        the way if set to 2.

    exclude : str [OPTIONAL]
        Regex pattern of file *name* to exclude from the count.

    Returns
    -------
    int [dict]
        Total number of files, and optionally a dictionary of subdirectories
        and their number of files, if details=True.
    """
    if not isdir(target_dir):
        msg = "Target folder doesn't exist."
        logger.exception(msg)
        raise ValueError(msg)

    tot_num_files = 0
    detail_data = {}
    for dirpath, dirnames, filenames in os.walk(target_dir):
        if exclude:
            filenames = [fname for fname in filenames
                         if not re.match(exclude, fname)]

        num_files = len(filenames)

        if details:
            rel_dirpath = dirpath.replace(target_dir, "")
            detail_data[rel_dirpath] = num_files
            if verbose:
                print("{} files found in {}".format(num_files, rel_dirpath))
                if verbose > 1:
                    msg = "Following files found in {}: {}".format(rel_dirpath,
                                                                   filenames)
                    print(msg)

        tot_num_files += num_files

    if details:
        return tot_num_files, detail_data
    else:
        return tot_num_files


def get_dir_sizes_cached(dir_path_list, cache_filepath="", cache=None,
                         unit="MB", run_parallel=True):
    """ Cached version of get_dir_size to avoid wasting time collecting
    readonly dir sizes unnecessarily.

    This assumes that the directories are readonly, and that their sizes can't
    change. Users can specify a cache URL (filepath) to read from/store to, or
    build their own cache implementation, following the
    :class:`app_common.apptools.cache.BaseCache` interface.

    Parameters
    ----------
    dir_path_list : list(str) or str
        List of paths to directories to compute the size of.

    cache_filepath : str, optional
        Path to the file the cache is stored in. Ignored if a custom cache is
        provided.

    cache : app_common.apptools.base_cache.BaseCache, optional
        Implementation of a custom cache to use to lookup/store directory size
        values.

    unit : str, optional
        Unit of the results. Supported values are 'B', 'KB', 'MB' and 'GB'.

    run_parallel : bool, optional
        Whether to use a multi-processing pool to compute all folder sizes.

    Returns
    -------
    list
        List of the sizes, in the same order as the `dir_path_list` argument.
    """
    from app_common.apptools.cache.txt_file_cache import SingleTxtFileDataCache

    if isinstance(dir_path_list, str):
        dir_path_list = [dir_path_list]

    if cache is None and cache_filepath:
        cache = SingleTxtFileDataCache(url=cache_filepath,
                                       auto_initialize=True)
        cache_created = True
    else:
        cache_created = False

    if cache:
        new_dirs = [dir_path for dir_path in dir_path_list
                    if dir_path not in cache]
    else:
        new_dirs = dir_path_list

    msg = "Found {} folders whose size is to be computed:\n{}."
    msg = msg.format(len(new_dirs), "\n    ".join(new_dirs))
    logger.info(msg)

    if len(new_dirs) > 1 and run_parallel:
        import multiprocessing as mp
        pool = mp.Pool()
        sizes_in_bytes = pool.map(partial(get_dir_size, unit="B"), new_dirs)
    else:
        sizes_in_bytes = [get_dir_size(fold, unit="B") for fold in new_dirs]

    factor = BYTE_UNIT_FACTORS[unit]
    if cache:
        for dir_path, size_in_bytes in zip(new_dirs, sizes_in_bytes):
            cache.set_value(dir_path, size_in_bytes)

        # Once all requests fulfilled, write new cache to disk if necessary
        if cache_created:
            cache.close()

        return [cache.get_value(dir_path)*factor for dir_path in dir_path_list]
    else:
        return [size * factor for size in sizes_in_bytes]
