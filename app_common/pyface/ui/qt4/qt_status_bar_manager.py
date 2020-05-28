
from traits.api import Int, Str
from pyface.ui.qt4.action.status_bar_manager import StatusBarManager


class QtStatusBarManager(StatusBarManager):
    """ A status bar manager realizes itself in a status bar control. """

    # Duration of appearance of the messages
    message_duration_ms = Int

    # Qt styling of the status bar
    style_sheet = Str

    def _style_sheet_changed(self, value):
        if self.status_bar:
            self.status_bar.setStyleSheet("QStatusBar{%s}" % value)

    def _show_messages(self):
        """ Display the list of messages. """

        # FIXME v3: At the moment we just string them together but we may
        # decide to put all but the first message into separate widgets.  We
        # probably also need to extend the API to allow a "message" to be a
        # widget - depends on what wx is capable of.
        self.status_bar.showMessage("  ".join(self.messages),
                                    msecs=self.message_duration)
