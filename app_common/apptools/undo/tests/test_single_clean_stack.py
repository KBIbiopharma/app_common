from app_common.apptools.undo.single_clean_state_command_stack import \
    SingleCleanStateCommandStack
from apptools.undo.api import UndoManager
from traits.api import Int
from apptools.undo.api import AbstractCommand
from traits.testing.unittest_tools import unittest, UnittestTools


class SimpleCommand(AbstractCommand):

    name = "Increment by 1"

    data = Int

    def do(self):
        self.redo()

    def redo(self):
        self.data += 1

    def undo(self):
        self.data -= 1


class TestSingleCleanStateCommandStack(unittest.TestCase, UnittestTools):
    def setUp(self):
        self.stack = SingleCleanStateCommandStack()
        undo_manager = UndoManager()
        self.stack.undo_manager = undo_manager
        self.command = SimpleCommand()

    # New tests ---------------------------------------------------------------

    def test_updated(self):
        with self.assertTraitChanges(self.stack, 'updated', count=1):
            self.stack.push(self.command)
        with self.assertTraitChanges(self.stack, 'updated', count=1):
            self.stack.undo()
        with self.assertTraitChanges(self.stack, 'updated', count=1):
            self.stack.redo()

    def test_save_push_save_undo_is_dirty(self):
        # This is the behavior that is different from the default apptools
        # implementation
        self.stack.push(self.command)

        self.stack.clean = True
        self.stack.push(self.command)
        self.stack.clean = True
        self.stack.undo()
        self.assertFalse(self.stack.clean)

    def test_empty_stack_is_always_clean(self):
        self.assertTrue(self.stack.clean)

    def test_stack_cannot_be_dirty(self):
        with self.assertRaises(ValueError):
            self.stack.clean = False
        self.assertTrue(self.stack.clean)

    def test_cleaning_an_empty_stack_saves_state(self):
        # Set clean state after single command
        self.stack.push(self.command)
        self.stack.clean = True

        # Set clean state after undoing to empty stack
        self.stack.undo()
        self.stack.clean = True

        # Make sure the empty state is recognized as the clean state.
        self.stack.redo()
        self.assertFalse(self.stack.clean)

    def test_initial_location_can_be_dirty(self):
        self.stack.push(self.command)
        self.stack.clean = True

        self.stack.undo()
        self.assertFalse(self.stack.clean)

    # Original cleanliness tests ----------------------------------------------

    def test_empty_stack_is_clean(self):
        self.assertTrue(self.stack.clean)

    def test_non_empty_stack_is_dirty(self):
        self.stack.push(self.command)
        self.assertFalse(self.stack.clean)

    def test_make_clean(self):
        # This makes it dirty by default
        self.stack.push(self.command)
        # Make the current tip of the stack clean
        self.stack.clean = True
        self.assertTrue(self.stack.clean)

    def test_make_dirty_by_adding_command(self):
        # Start from a clean state:
        self.stack.push(self.command)
        self.stack.clean = True

        self.stack.push(self.command)
        self.assertFalse(self.stack.clean)

    def test_save_push_undo_is_clean(self):
        self.stack.push(self.command)

        self.stack.clean = True
        self.stack.push(self.command)
        self.stack.undo()
        self.assertTrue(self.stack.clean)

    def test_save_push_undo_redo_is_dirty(self):
        self.stack.push(self.command)

        self.stack.clean = True
        self.stack.push(self.command)
        self.stack.undo()
        self.stack.redo()
        self.assertFalse(self.stack.clean)

    def test_push_undo_save_redo_is_dirty(self):
        self.stack.push(self.command)
        self.stack.undo()
        self.stack.clean = True
        self.stack.redo()
        self.assertFalse(self.stack.clean)
