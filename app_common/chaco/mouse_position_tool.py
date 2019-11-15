""" Tool and overlay to display the mouse position in an overlay.
"""
from traits.api import Any, Callable, Enum, Instance, on_trait_change
from chaco.api import BaseTool, TextBoxOverlay


def add_mouse_position_tool(plot, move_callback=None, include_overlay=False,
                            message_for_data=None):
    """Add moue position tool and overlay to a plot.

    The inspector tool and overlay are added to the plot's `tools` and
    `overlays` lists and both objects are returned for further use.
    """
    # Attach the inspector tool
    inspector = MousePositionTool(plot, move_callback=move_callback)
    plot.tools.append(inspector)

    # Create and attach the inspector overlay
    if include_overlay:
        overlay = MousePositionOverlay(plot, inspector=inspector,
                                       message_for_data=message_for_data)
        plot.overlays.append(overlay)
    else:
        overlay = None

    return inspector, overlay


class MousePositionTool(BaseTool):
    """ Tool that reports the current data location of the cursor.
    """
    #: The coordinates of the cursor.
    data_coord = Any

    #: Function to be called on move events
    move_callback = Callable

    def normal_mouse_move(self, event):
        plot = self.component
        self.data_coord = plot.map_data((event.x, event.y))
        if self.move_callback:
            self.move_callback(self.data_coord)

    def normal_mouse_leave(self, event):
        self.data_coord = None


class MousePositionOverlay(TextBoxOverlay):
    """ Overlay for displaying information from a DataInspectorTool.
    """

    #: The inspector tool which has an index into the
    inspector = Instance(MousePositionTool)

    #: Function which takes and index and returns an info string.
    message_for_data = Callable

    #: The default state of the overlay is invisible (overrides PlotComponent).
    visible = False

    #: Whether the overlay should auto-hide and auto-show based on the
    #: tool's location, or whether it should be forced to be hidden or visible.
    visibility = Enum("auto", True, False)

    # Customize appearance
    border_color = 'none'
    text_color = 'white'
    bgcolor = 'black'
    alpha = 0.6

    @on_trait_change('inspector:data_coord')
    def _index_updated(self):
        data_coord = self.inspector.data_coord
        if data_coord is None:
            self.text = ""
        else:
            self.text = self.message_for_data(data_coord)

        self.visible = len(self.text) > 0
        self.component.request_redraw()

    def _visible_changed(self):
        self.component.request_redraw()

    def _message_for_data_default(self):
        return lambda x: "x: {:.3f}, y: {:.3f}".format(*x)
