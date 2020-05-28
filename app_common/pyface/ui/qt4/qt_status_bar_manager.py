
from traits.api import Int, Str
from pyface.ui.qt4.action.status_bar_manager import StatusBarManager


class QtStatusBarManager(StatusBarManager):
    """ A status bar manager realizes itself in a status bar control.

    Subclassed from the Qt implementation to expose the ability to optionally
    change the style sheet of the widget and time messages out.
    """

    # Duration of appearance of the messages in milliseconds
    message_duration_ms = Int

    # Qt styling of the status bar
    style_sheet = Str

    def _style_sheet_changed(self, value):
        if self.status_bar:
            self.status_bar.setStyleSheet("QStatusBar{%s}" % value)

    def _show_messages(self):
        """ Display the list of messages with the optional timing.
        """
        self.status_bar.showMessage("  ".join(self.messages),
                                    msecs=self.message_duration)
