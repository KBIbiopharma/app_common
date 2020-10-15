# -*- coding: utf-8 -*-
""" Utilities providing new custom assertions to support IO serialization unit
tests.
"""
from traits.api import HasTraits

from app_common.traits.assertion_utils import assert_has_traits_almost_equal, \
    assert_values_almost_equal
from app_common.apptools.testing_utils import \
    reraise_traits_notification_exceptions
from app_common.apptools.io.reader_writer import save_object, load_object
from app_common.apptools.testing_utils import temp_fname
from app_common.apptools.io.serializer import serialize
from app_common.apptools.io.deserializer import deserialize


def assert_roundtrip_identical(obj, serial_func=None, deserial_func=None,
                               **kwargs):
    """ Serialize and deserialize an object and assert that the resulting
    object is identical to the input object.

    Parameters
    ----------
    obj : any
        Object to serialize/deserialize.

    serial_func : callable
        Function to serialize the object to serial data.

    deserial_func : callable
        Function to deserialize data into an object. Should return a collection
        where the deserialized object is the first element.

    kwargs : dict
        Additional keyword arguments passed to `is_has_traits_almost_equal`.

    Returns
    -------
    Any
        Object serialized and recreated is returned if user needs to run
        additional tests.
    """
    if serial_func is None:
        serial_func = serialize
    if deserial_func is None:
        deserial_func = deserialize

    serial_data, array_collection = serial_func(obj)
    # Make sure that when rebuiding the new objects, no listener is
    # breaking:
    with reraise_traits_notification_exceptions():
        new_object = deserial_func(serial_data,
                                   array_collection=array_collection)[0]

    if isinstance(obj, HasTraits):
        assert_has_traits_almost_equal(obj, new_object, **kwargs)
    else:
        assert_values_almost_equal(obj, new_object, **kwargs)
    return new_object


def assert_file_roundtrip_identical(obj, save_func=None, load_func=None,
                                    target_dir=None, **kwargs):
    """ Serialize and deserialize an object and assert that the resulting
    object is identical to the input object.

    obj : any
        Object to serialize/deserialize.

    save_func : callable
        Function to store the object to file.

    load_func : callable
        Function to load the object from file. It should return a collection
        where the deserialized object is the first element.

    kwargs : dict
        Additional keyword arguments passed to `is_has_traits_almost_equal`.

    Returns
    -------
    Any
        Object serialized and recreated is returned if user needs to run
        additional tests.
    """
    if save_func is None:
        save_func = save_object

    if load_func is None:
        load_func = load_object

    with temp_fname(target_dir=target_dir) as fname:
        save_func(fname, obj)
        # Make sure that when rebuiding the new objects, no listener is
        # breaking:
        with reraise_traits_notification_exceptions():
            new_object = load_func(fname)[0]

        if isinstance(obj, HasTraits):
            assert_has_traits_almost_equal(obj, new_object, **kwargs)
        else:
            assert_values_almost_equal(obj, new_object, **kwargs)
