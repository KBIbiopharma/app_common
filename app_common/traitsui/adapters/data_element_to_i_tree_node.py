import logging
from traits.api import Instance, List, Property, TraitDictObject, \
    TraitListObject
from traitsui.api import ITreeNodeAdapter
from traitsui.menu import Menu, Separator
from traitsui.qt4.tree_editor import DeleteAction, RenameAction

from app_common.model_tools.data_element import DataElement
from app_common.traits.has_traits_utils import trait_dict

logger = logging.getLogger(__name__)


class DataElementToITreeNode(ITreeNodeAdapter):
    """ Adapts a general DataElement to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any DataElement.
    """

    adaptee = Instance(DataElement)

    children = Property(List, depends_on="adaptee")

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def allows_children(self):
        return True

    def has_children(self):
        return self.children != []

    def get_children(self):
        return self.children

    def _get_children(self):
        """ Collecting all traits that are ChromatographyData, None
        (uninitialized data) or lists/dictionaries of these things.
        """
        children = []
        adaptee_content = trait_dict(self.adaptee)
        for trait_name, attr in adaptee_content.items():
            if isinstance(attr, DataElement):
                children.append(attr)
            elif isinstance(attr, TraitListObject):
                # Only pick up lists of ChromData
                if not attr:
                    children.append(attr)
                elif isinstance(attr[0], DataElement):
                    children.append(attr)
                elif isinstance(attr[0], list) or isinstance(attr[0], dict):
                    raise AttributeError(
                        "Unexpected list of lists or list of dicts when "
                        "crawling the DataElement tree")

            elif isinstance(attr, TraitDictObject):
                # Only pick up dict of ChromData
                if not attr:
                    children.append(attr)
                elif isinstance(attr.values()[0], DataElement):
                    children.append(attr)
                elif isinstance(attr.values()[0], list) or \
                        isinstance(attr.values()[0], dict):
                    msg = ("Unsupported dict of lists or dict of dicts when "
                           "crawling the DataElement tree")
                    logger.exception(msg)
                    raise AttributeError(msg)

        adaptee_klass = self.adaptee.__class__.__name__
        msg = "Collected {} as children of a {}".format(children,
                                                        adaptee_klass)
        logger.debug(msg)
        return children

    def get_label(self):
        """ Gets the tree node label.
        """
        return self.adaptee.name

    def set_label(self, label):
        """ Additional actions while setting the tree node label.
        """
        self.adaptee.name = label

    def get_tooltip(self):
        return "{} ({})".format(self.adaptee.name,
                                self.adaptee.__class__.__name__)

    def get_menu(self):
        # See TreeEditor on_context_menu code to understand the context the
        # actions are evaluated in.

        # FIXME The order of actions in the drop down are not easily controlled
        # When the order can be controlled, it should be set per comments
        # on PR#586.
        actions = self._standard_menu_actions()
        actions.extend(self._non_standard_menu_actions())
        return Menu(*actions)

    def _standard_menu_actions(self):
        """ Returns the standard actions for the context menu.
        """
        # An object can be deleted and renamed by default:
        actions = [RenameAction, Separator(), DeleteAction]
        return actions

    def _non_standard_menu_actions(self):
        """ Returns non standard menu actions for the context menu.
        """
        actions = []
        return actions

    def can_rename_me(self):
        """ Returns whether the object can be renamed.
        """
        return True

    def can_delete(self):
        """ Returns whether the object's children can be deleted.
        """
        return True

    def can_delete_me(self):
        """ Returns whether the object can be deleted.
        """
        return True

    def confirm_delete(self):
        """ Checks whether a specified object can be deleted.

        Returns
        -------
        * **True** if the object should be deleted with no further prompting.
        * **False** if the object should not be deleted.
        * Anything else: Caller should take its default action (which might
          include prompting the user to confirm deletion).
        """
        return 'Confirm'
