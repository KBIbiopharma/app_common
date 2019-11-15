from apptools.undo.command_stack import _StackEntry, CommandStack
from traits.api import Bool, Event, Property, WeakRef


class SingleCleanStateCommandStack(CommandStack):
    """ This version of the command stack has only 1 stack entry that is clean.

    It starts with assuming that the empty stack state is the clean one. If
    another command is set to be the clean state, the stack is dirty anywhere
    else. Note that in this implementation, the stack can never be set to dirty
    everywhere.

    This implementation also adds an event that gets triggered when push,
    redo and undo are called. That allows to listen to changes to the stack.
    """
    clean = Property(Bool)

    #: Command entry that was last set to clean
    _clean_command = WeakRef(_StackEntry, allow_none=True)

    #: Listenable event triggered by any move along the stack: push, undo, redo
    updated = Event

    def push(self, command):
        result = super(SingleCleanStateCommandStack, self).push(command)
        self.updated = True
        return result

    def redo(self, sequence_nr=0):
        result = super(SingleCleanStateCommandStack, self).redo(sequence_nr)
        self.updated = True
        return result

    def undo(self, sequence_nr=0):
        result = super(SingleCleanStateCommandStack, self).undo(sequence_nr)
        self.updated = True
        return result

    def _get_clean(self):
        """ Is the stack clean (current location is location declared clean)?
        """
        if self._index == -1:
            # Index = -1 is null, not the last stack entry
            current_location = None
        else:
            current_location = self._stack[self._index]

        clean = current_location is self._clean_command

        return clean

    def _set_clean(self, clean):
        """ Set the clean state of the stack. """
        if not clean:
            raise ValueError("SingleCleanStateCommandStack doesn't support "
                             "setting the entire stack to a dirty state.")

        if self._index >= 0:
            self._clean_command = self._stack[self._index]
        else:
            # self._index is -1: current location is nowhere in the stack
            self._clean_command = None
