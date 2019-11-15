from os.path import splitext


def generate_is_ext_file(ext_list):
    """ Generate function to tests if the extension of a file is in a list.

    Parameters
    ----------
    ext_list : Iterable
        List (better set if a large number of items) of extensions to test a
        file against.
    """
    for i, ext in enumerate(ext_list):
        if not ext.startswith("."):
            ext_list[i] = "." + ext

    def func(filename):
        return splitext(filename)[1] in ext_list

    func.__doc__ = "Test if a file name/path has a {} extension.".format(ext)
    return func


is_py_file = generate_is_ext_file({".py"})

is_csv_file = generate_is_ext_file({".csv"})

is_excel_file = generate_is_ext_file({".xlsx", ".xls"})

is_hdf_file = generate_is_ext_file({".h5", ".hdf5"})
