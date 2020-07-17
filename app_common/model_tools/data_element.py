from uuid import UUID, uuid4

from traits.api import Bool, HasStrictTraits, Instance

from app_common.traits.custom_trait_factories import Key


class DataElement(HasStrictTraits):
    """ Base class for all the data objects.

    Provides a base class describing the API for all the data objects to be
    viewed or edited in the GUI application
    """

    #: The required user visible name for the object.
    name = Key()

    #: determines whether user can edit object in UI (most importantly for)
    #: Simulation objects which will be asynchronously updated when run through
    #: Cadet, during which we don't want the user to change them.
    editable = Bool(True)

    #: A unique ID for the object
    uuid = Instance(UUID)

    def traits_view(self):
        from traitsui.api import Item, View

        return View(
            Item("name")
        )

    # Initialization methods --------------------------------------------------

    def _uuid_default(self):
        return uuid4()

    def copy(self, copy="shallow"):
        """ Returns a copy of the current object, with a different ID.

        Parameters
        ----------
        copy : str
            Deep or shallow copy? Supported values are `shallow` and `deep`.
        """
        new_obj = self.clone_traits(copy=copy)
        new_obj.name = self.name + "COPY"
        new_obj.uuid = uuid4()
        return new_obj
