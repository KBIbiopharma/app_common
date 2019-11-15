""" String manipulation tools.
"""


def add_suffix_if_exists(candidate, existing_names, suffix_patt="_v{}"):
    """ Append a auto-incrementing suffix to a candidate name as long as the
    candidate name is in the existing names.

    Parameters
    ----------
    candidate : str
        Candidate name to add a suffix to if present in the existing names.

    existing_names : list(str)
        List of names that the output path cannot be.

    suffix_patt : str
        String containing {} that will be used to build and auto-incrementing
        suffix (using str.format).

    Returns
    -------
    str
        New name, not present in existing_names.
    """
    i = 1
    while candidate in existing_names:
        if i > 1:
            # Remove the previous suffix
            old_suffix = suffix_patt.format(i)
            candidate = candidate[:-len(old_suffix)]

        i += 1
        new_suffix = suffix_patt.format(i)
        candidate += new_suffix

    return candidate


def sanitize_string(string, special_chars=None, replace_with="_"):
    """ Replace special characters in a string by a character ('_' by default).

    Parameters
    ----------
    string : str
        String to sanitize.

    special_chars : iterable of string, optional
        Special characters to remove from the string.

    replace_with : str
        String to replace each bad character with.
    """
    from .filepath_utils import string2filename, SPECIAL_CHARACTERS

    if special_chars is None:
        special_chars = SPECIAL_CHARACTERS + ".~"

    return string2filename(string, special_chars=special_chars,
                           replace_with=replace_with)


def fuzzy_string_search_in(element, collection, transform="std", ignore=" _"):
    """ Search if a string is loosely in a collection of strings.

    Parameters
    ----------
    element : str
        Element to search for.

    collection : iterable of strings
        Collection of element to search through for a fuzzy match.

    transform : callable or "std" or None
        Customized transformation applied to (both) elements before testing for
        equality (to implement the fuzzy matching). Pass "std" to use the
        default transformation (lower case and remove spaces and underscores)
        or None to apply no transformation (exact match necessary).

    ignore : iterable of string
        List of characters to remove in standard transformation. Default is " "
        and "_".

    Returns
    -------
    str or None
        Returns the element in the collection that fuzzy matches the element
        passed, if any is found, or None otherwise.
    """
    if transform is None:
        def transform(x):
            return x
    elif transform == "std":
        def transform(x):
            normalized = x.lower()
            for char in ignore:
                normalized = normalized.replace(char, "")
            return normalized

    for col_element in collection:
        if transform(col_element) == transform(element):
            return col_element


def format_array(arr, precision=4):
    """ Create a string representation of a numpy array with less precision
    than the default.

    Parameters
    ----------
    arr : array
        Array to be converted to a string

    precision : int
        Number of significant digit to display each value.

    Returns
    -------
    str
        Nice string representation of the array.
    """
    if arr is None:
        return ""

    formatting_str = "{0:." + str(precision) + "g}"
    str_values = [formatting_str.format(float(val)) for val in arr]
    content = ", ".join(str_values)
    return "[" + content + "]"
