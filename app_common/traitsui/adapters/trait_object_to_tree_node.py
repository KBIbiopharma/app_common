import logging

from traits.api import Callable, Instance, TraitDictObject, TraitListObject
from traitsui.api import Action, ITreeNodeAdapter, Menu
from traitsui.qt4.tree_editor import PasteAction, Separator

logger = logging.getLogger(__name__)


class TraitListObjectToTreeNode(ITreeNodeAdapter):
    """ Adapts a list of objects to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any TraitList.
    """

    adaptee = Instance(TraitListObject)

    children_changed_listener = Callable

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def allows_children(self):
        return True

    def has_children(self):
        return len(self.adaptee) != 0

    def get_children(self):
        return self.adaptee

    def get_label(self):
        # A traitList object has a name attribute given by its parent class
        name = self.adaptee.name
        return name.replace("_", " ").capitalize()

    def get_icon(self, is_expanded):
        if is_expanded:
            return '<open>'
        else:
            return '<group>'

    # Menu related methods ----------------------------------------------------

    def get_menu(self):
        """ All lists should be able to be pasted into. Some support creating
        new objects.
        """
        actions = [PasteAction]

        if hasattr(self.adaptee, "add_new_entry"):
            actions.extend([
                Separator(),
                Action(name="Create New...", action="object.add_new_entry"),
            ])
        menu = Menu(*actions)
        return menu

    def can_copy(self):
        """ Returns whether the object's children can be copied.
        """
        return True

    def can_add(self, instance_type):
        """ Returns whether the object's children can be pasted from clipboard.
        """
        try:
            list_trait = self.adaptee.trait
            list_element_trait_type = list_trait.item_trait.trait_type
            allowed_type = list_element_trait_type.klass
            return issubclass(instance_type, allowed_type)
        except AttributeError as e:
            msg = "Failed to recover the expected class. Error was {}."
            msg = msg.format(e)
            logger.error(msg)
        return False

    def append_child(self, child):
        """ Appends a child to the object's children.
        """
        child = self._prepare_to_append(child)
        if child is not None:
            self.adaptee.append(child)

    def _prepare_to_append(self, obj):
        """ Prepare to append to a list.

        Parameters
        ----------
        obj : any
            Object to review and optionally modify to prepare it to be appended
            to current list.

        Returns
        -------
        bool
            Whether the object is ready to be appended or not.
        """
        return True

    def can_rename(self):
        """ Returns whether the object's children can be renamed. """
        return True

    def can_delete(self):
        """ Returns whether the object's children can be deleted. """
        return True

    def delete_child(self, index):
        """ Deletes a child at a specified index from the object's children.
        """
        self.adaptee.remove(self.adaptee[index])

    # Listener related methods ------------------------------------------------

    def when_children_changed(self, listener, remove):
        """ This takes care of propagating a change in the children of this
        list back to the tree editor.

        Parameters
        ----------
        listener : Callable
            TreeEditor listener that must be called to force a repaint of the
            tree.

        remove : Bool
            Whether we should add a new listener to call the tree editor
            listener because the tree is being built, or removed because the
            tree editor is being cleaned up.
        """
        if remove:
            self.children_changed_listener = None
        else:
            self.children_changed_listener = listener

        # NOTE: adaptee.object() refers to the parent object containing the
        # adapted list.
        # When the list is modified, the event is sent to the parent object
        # `obj`. So listen for changes to the parent object and invoke the
        # tree listener.
        name = "{}_items".format(self.adaptee.name)
        obj = self.adaptee.object()
        obj.on_trait_change(self._children_changed, name=name, remove=remove,
                            dispatch='ui')

    def _children_changed(self, object, name, event):
        """ This calls the tree editor's listener with the appropriate
        arguments, which is the object that changed, the elements that were
        added as children and removed from children.
        """
        name = self.adaptee.name
        self.children_changed_listener(getattr(object, name), '', event)

    def when_children_replaced(self, listener, remove):
        """ This takes care of propagating to the tree editor the fact that
        this list is replaced.

        FIXME: This still needs to be tested.

        Parameters
        ----------
        see when_children_changed
        """
        obj = self.adaptee.object()
        obj.on_trait_change(self._children_changed, name=self.adaptee.name,
                            remove=remove, dispatch='ui')


class TraitDictObjectToTreeNode(ITreeNodeAdapter):
    """ Adapts a Traits dictionary of objects to an ITreeNode.

    This assumes that the values are of the same nature, and therefore picks
    the name of the node from the type of the first values.

    FIXME: Overwriting the when_children_changed and when_children_replaced
    still needs to take place for this to propagate information.
    """

    adaptee = Instance(TraitDictObject)

    children_changed_listener = Callable

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def allows_children(self):
        return True

    def has_children(self):
        return True

    def get_children(self):
        return self.adaptee.values()

    def get_label(self):
        # A traitDict object has a name attribute given by its parent class
        return self.adaptee.name.capitalize()
