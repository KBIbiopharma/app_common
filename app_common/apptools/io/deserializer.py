""" Module containing the deserializer api function and supporting classes.

The deserializers are versioned and the ones in this module correspond to the
latest protocol. Old versions of deserializers that were updated are stored in
the legacy_deserializers dict.
"""
import logging
from six import string_types

from traits.api import HasStrictTraits, Type

from .serialization_utils import sanitize_class_name

logger = logging.getLogger(__name__)


class NoDeserializerFoundError(ValueError):
    pass


class deSerializer(HasStrictTraits):
    """ Base class for all other deserialization related classes.

    Contains the generic dynamic methods for deserializing some data back into
    a class instance.
    """
    #: Default version of the deserializer
    protocol_version = 0

    #: Class attr with all ndarrays mapped to their id in the serial data.
    array_collection = {}

    #: Dict mapping ids (set at serialization) to instances already
    #: deserialized, in case the same object needs to be pointed to.
    instance_collection = {}

    #: Class level attribute to lookup available deserializers (same protocole)
    deserializer_map = {}

    #: Map between (object type, old_protocole) and deserializers classes
    legacy_deserializers = {}

    #: Whether at least 1 legacy deserializer has been used
    legacy_file = False

    @classmethod
    def set_array_collection(cls, array_collection):
        # Modify the dict in place to make sure all subclasses share the same
        # container:
        cls.array_collection.clear()
        cls.array_collection.update(array_collection)

    @classmethod
    def instance_lookup(cls, obj_id):
        """ Lookup if an object with provided id has been deserialized already.

        Parameters
        ----------
        obj_id : any immutable type
            Id, assigned at serialization, of the object to deserialize. This
            id is expected to be found as one of the keys of the
            instance_collection class attribute.

        Returns
        -------
        The instance of the object if the id has been encountered, and stored
        in the instance_collection class attribute. Returns None otherwise.
        """
        obj = None
        if cls.instance_collection is None:
            cls.instance_collection = {}

        if obj_id in cls.instance_collection:
            obj = cls.instance_collection[obj_id]

        return obj

    def deserialize(self, serial_data):
        """ Actual deserialization of the serialized data.

        Parameters
        ----------
        serial_data : dictionary
            serial_data is a dictionary with the following items.
            'class_metadata' : Information about the class to be instantiated
            'data' : Contains arguments required for instantiating the class

        Returns
        -------
        A new class instance for the serial_data.
        """
        deserializer = self.select_deserializer(serial_data)
        obj = deserializer.build_object(serial_data)
        return obj

    def select_deserializer(self, serial_data):
        """ Returns the deserializer class appropriate for the provided serial
        data. Raises a ValueError if none is found.

        Parameters
        ----------
        serial_data : dictionary or basic type
            serial_data either a basic object that can be instanciated
            automatically or a dictionary with the following items:
            'class_metadata' : Information about the class to be instantiated
            'data' : Contains arguments required for instantiating the class
        """
        if isinstance(serial_data, dict) and 'class_metadata' in serial_data:
            klass = sanitize_class_name(serial_data['class_metadata']['type'])
            written_version = serial_data["class_metadata"]["version"]
        else:
            # Basic type: no metadata, they are stored as themselves
            written_version = None
            klass = sanitize_class_name(serial_data.__class__.__name__)

        try:
            default_deserializer = self.deserializer_map[klass+'DeSerializer']
        except (KeyError, AttributeError) as e:
            msg = "No active deserializer was found for class {}. Now " \
                  "searching in the legacy deserializers... (Error was {}.)"
            logger.warning(msg.format(klass, e))

            default_deserializer = None
            use_default = False
            current_version = None
        else:
            current_version = default_deserializer.protocol_version
            use_default = (written_version is None or
                           current_version == written_version)

        if use_default:
            deserializer = default_deserializer
        elif current_version is not None and current_version < written_version:
            msg = ("Trying to load a {} version {} but the most recent "
                   "deserializer available is version {}. This file was "
                   "created with a newer version of the software. It will need"
                   "to be updated to be able to load this file.")
            msg = msg.format(klass, written_version, current_version)
            logger.exception(msg)
            raise NoDeserializerFoundError(msg)
        else:
            # Search for a deserializer support the version 'written_version'
            old_deserializer_dict = self.legacy_deserializers.get(klass, None)

            if old_deserializer_dict is None:
                msg = "Unable to find a legacy deserializer for a {}.".format(
                    klass)
                logger.exception(msg)
                raise NoDeserializerFoundError(msg)

            deSerializer.legacy_file = True
            deserializer = old_deserializer_dict.get(written_version, None)
            if deserializer is None:
                versions = sorted(old_deserializer_dict.keys())
                msg = "Unable to find a deserializer for a {} version {}. " \
                      "Available versions are {}."
                msg = msg.format(klass, written_version, versions)
                logger.exception(msg)
                raise NoDeserializerFoundError(msg)

        return deserializer()

    def build_object(self, serial_data):
        """ Recreate class objects from the serialized data.

        Deserialize all arguments to the class constructor for the target data
        type, and build the instance.

        Parameters
        ----------
        serial_data : dictionary
            serial_data is a dictionary with the following items.
            'class_metadata' : Information about the class to be instantiated
            'data' : Contains arguments required for instantiating the class

        Returns
        ------
        A class instance for the serial_data, whether from the instance_lookup
        or a newly created one if the id has never been encountered.
        """
        data = serial_data.pop('data', None)
        metadata = serial_data.pop('class_metadata', None)
        obj_id = metadata['id']

        constructor_data = {'metadata': metadata}
        metadata_name = None

        if data is not None:
            data = self.deserialize(data)
            constructor_data['args'] = data

        if serial_data:
            instance_data = self.deserialize(serial_data)
            if instance_data.get('metadata'):
                metadata_name = instance_data['metadata'].get('name')
            constructor_data['kwargs'] = instance_data

        if obj_id is None:
            instance = self.get_instance(constructor_data)

        else:
            # For objects that were saved with a unique "id", lookup
            # if that object has already been built
            instance = self.instance_lookup(obj_id)
            if instance is None:
                instance = self.get_instance(constructor_data)
                self.instance_collection[obj_id] = instance

        # FIXME: Instance metadata name is overwritten with the instance.name
        # in the ChromatographyData  __init__ so reassign name here. Better way
        # to do it?
        if metadata_name:
            instance.metadata['name'] = metadata_name
        return instance


class simpleObjDeSerializer(deSerializer):

    klass = Type

    def get_instance(self, constructor_data):
        instance = self.klass(**constructor_data['kwargs'])
        return instance


class dataElementDeSerializer(simpleObjDeSerializer):
    def _klass_default(self):
        from app_common.model_tools.data_element import DataElement
        return DataElement


class basicTypeDeSerializer(deSerializer):
    def build_object(self, serial_data):
        # Convert unicode to string ... required for existing code
        if isinstance(serial_data, string_types):
            serial_data = str(serial_data)

        instance = type(serial_data)(serial_data)
        return instance


class boolDeSerializer(basicTypeDeSerializer):
    pass


class floatDeSerializer(basicTypeDeSerializer):
    pass


class float64DeSerializer(basicTypeDeSerializer):
    """ Deserialization for numpy.float64
    """
    def build_object(self, serial_data):
        instance = float(serial_data)
        return instance


class timestampDeSerializer(basicTypeDeSerializer):
    """ Deserialization for pandas.tslib.Timestamp.
    """
    def build_object(self, serial_data):
        from pandas import Timestamp
        instance = Timestamp(serial_data['data'])
        return instance


class dateDeSerializer(basicTypeDeSerializer):
    """ Deserialization for datetime.date.
    """
    def build_object(self, serial_data):
        from datetime import date
        instance = date(*serial_data['data'])
        return instance


class intDeSerializer(basicTypeDeSerializer):
    pass


class longDeSerializer(basicTypeDeSerializer):
    pass


class strDeSerializer(basicTypeDeSerializer):
    pass


class unicodeDeSerializer(basicTypeDeSerializer):
    pass


class noneTypeDeSerializer(basicTypeDeSerializer):
    def build_object(self, serial_data):
        return serial_data


class dictDeSerializer(deSerializer):
    def build_object(self, serial_data):
        deserialized_dict = {}
        if 'class_metadata' in serial_data and \
                'dict' in serial_data['class_metadata']['type']:
            serial_data.pop('class_metadata', None)
        for key, val in serial_data.items():
            deserialized_dict.update({key: self.deserialize(val)})
        return deserialized_dict


class seriesDeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        from pandas.core.series import Series
        instance = Series(constructor_data['args'],
                          index=constructor_data['kwargs']['index'])
        return instance


class dataFrameDeSerializer(deSerializer):
    protocol_version = 1

    def build_object(self, serial_data):
        filename = serial_data['class_metadata']['filename']
        df_id = serial_data['class_metadata']['id']
        return self.array_collection[(filename, df_id)]


class traitDictObjectDeSerializer(deSerializer):
    def build_object(self, serial_data):
        # TraitsDict object is deserialized as a regular dict because the
        # constructors of HasTraits objects expect dictionaries not
        # TraitDictObjects
        deserialized_dict = {}
        serial_data.pop('class_metadata', None)
        for key, val in serial_data.items():
            deserialized_dict.update({key: self.deserialize(val)})
        return deserialized_dict


class listDeSerializer(deSerializer):
    def build_object(self, serial_data):
        _list = []
        for item in serial_data:
            _list.append(self.deserialize(item))
        return _list


class setDeSerializer(deSerializer):
    def build_object(self, serial_data):
        _set = set()
        for item in serial_data["data"]:
            _set.add(self.deserialize(item))
        return _set


class ndarrayDeSerializer(deSerializer):
    protocol_version = 1

    def build_object(self, serial_data):
        filename = serial_data['class_metadata']['filename']
        arr_uuid = serial_data['class_metadata']['id']
        return self.array_collection[(filename, arr_uuid)]


class smartUnitDeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        from scimath.units.smart_unit import SmartUnit
        instance = SmartUnit(*constructor_data['args'])
        return instance


class traitListObjectDeSerializer(deSerializer):
    def build_object(self, serial_data):
        _list = []
        for item in serial_data['data']:
            deserializer = self.select_deserializer(item)
            _list.append(deserializer.build_object(item))
        return _list


class tupleDeSerializer(deSerializer):
    def build_object(self, serial_data):
        elements = []
        for item in serial_data['data']:
            deserializer = self.select_deserializer(item)
            elements.append(deserializer.build_object(item))
        return tuple(elements)


class unitDeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        import scimath.units.unit
        instance = getattr(scimath.units.unit,
                           constructor_data['metadata']['type'])(
                           *constructor_data['args'])
        # Set the unit.label because the Unit Class assigns
        # the label attribute equal to None when the Unit Class is constructed
        instance.label = constructor_data['kwargs']['label']
        return instance


class unitScalarDeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        import scimath.units.unit_scalar
        instance = getattr(scimath.units.unit_scalar,
                           constructor_data['metadata']['type'])(
                           constructor_data['args'],
                           **constructor_data['kwargs'])
        return instance


class unitArrayDeSerializer(unitScalarDeSerializer):
    """ Version 1 of the unitArray deserializer.
    """
    protocol_version = 1

    def build_object(self, serial_data):
        from scimath.units.unit_array import UnitArray

        filename = serial_data['class_metadata']['filename']
        array_id = serial_data['class_metadata']['id']
        data = self.array_collection.get((filename, array_id), None)
        units = self.deserialize(serial_data["units"])
        return UnitArray(data, units=units)


class uUIDDeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        from uuid import UUID
        instance = UUID(constructor_data['args'])
        return instance


def deserialize(serial_data, array_collection=None, klass=None,
                additional_deserializers=None):
    """ Functional entry point to deserialize any serial data.

    Note that this function resets the instance_collection class attribute, and
    should therefore not be called more than once for each file loading.

    Parameters
    ----------
    serial_data : dict
        All non-array data to rebuild the object.

    array_collection : dict
        Dictionary mapping all numpy arrays stored to an id in the serial data.

    klass : deSerializer [OPTIONAL]
        Implementation of the deserialization class. Can be passed for example
        to set the legacy_deserializers dict.

    additional_deserializers : dict
        Map between object class names and corresponding deserializer object to
        use to recreate the instance.

    Returns
    -------
    any, bool
        Object being deserialized and whether or not legacy deserializers were
        needed.
    """
    if klass is None:
        klass = deSerializer

    if array_collection is None:
        array_collection = {}

    if additional_deserializers is None:
        additional_deserializers = {}

    klass.instance_collection.clear()
    klass.legacy_file = False
    deserializer_map = {}
    # Additional serializers added afterwards, to allow projects to override
    # the way to serialize basic types:
    app_common_content = {key: val for key, val in globals().items()
                          if key.endswith("DeSerializer")}
    deserializer_map.update(app_common_content)
    deserializer_map.update(additional_deserializers)
    deserializer = klass()
    deserializer.deserializer_map.update(deserializer_map)
    deserializer.set_array_collection(array_collection)
    obj = deserializer.deserialize(serial_data['data'])
    return obj, klass.legacy_file
