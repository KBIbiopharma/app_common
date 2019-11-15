import logging

from traits.api import adapt, Any, Dict, Instance, Property, Str
from traitsui.api import ModelView, UI
from pyface.tasks.api import Editor
from pyface.api import information
from traits.adaptation.adaptation_error import AdaptationError

from app_common.model_tools.data_element import DataElement
from app_common.traitsui.crud_editor import DataElementCRUDEditor

logger = logging.getLogger(__name__)


class DataElementEditor(Editor):
    """ Editor for viewing and modifying a DataElement object via the TraitsUI
    view it provides. It invokes the view factories it knows to create the
    control it needs to display.

    This could have been done using pyface.tasks.traits_editor.TraitsEditor.
    Using this custom one because the create method in our case will invoke
    edit_traits on the CRUD editor around the view of the object being edited.
    """

    traits_ui = Instance(UI)

    # -------------------------------------------------------------------------
    # 'Editor' interface
    # -------------------------------------------------------------------------

    # The editor's user-visible name.
    name = Property(Str, depends_on="obj.name")

    # The tooltip to show for the editor's tab, if any.
    tooltip = Property(Str, depends_on="obj.name")

    # The toolkit-specific control that represents the editor.
    control = Any

    # The object that the editor is editing.
    obj = Instance(DataElement)

    #: The obj adapter to build a ModelView
    obj_view = Any

    #: CRUD editor parameters
    editor_kwargs = Dict

    # -------------------------------------------------------------------------
    # 'Editor' interface methods
    # -------------------------------------------------------------------------

    def create(self, parent):
        """ Create and set the toolkit-specific control that represents the
        editor.
        """
        self.control = self._create_control(parent)

    # -------------------------------------------------------------------------
    # Traits property methods
    # -------------------------------------------------------------------------

    def _get_name(self):
        return self.obj.name[:25]

    def _get_tooltip(self):
        return self.obj.name

    # -------------------------------------------------------------------------
    # Private interface.
    # -------------------------------------------------------------------------

    def _create_control(self, parent):
        """ Creates the view and then toolkit-specific control for the widget.
        """
        # Build the view for the object and embed inside the crud_editor to add
        # view controls
        try:
            self.obj_view = adapt(self.obj, ModelView)
        except AdaptationError:
            msg = "There are no registered view for a {}."
            msg = msg.format(type(self.obj))
            logger.warning(msg)
            information(None, msg)
            return

        crud_view = DataElementCRUDEditor(model_view=self.obj_view,
                                          **self.editor_kwargs)

        # Setting the kind and the parent allows for the ui to be embedded
        # within the parent UI
        self.traits_ui = crud_view.edit_traits(kind="subpanel", parent=parent)

        # Grab the Qt widget to return to the editor area
        control = self.traits_ui.control
        return control
