# -*- coding: utf-8 -*-

# Copyright Martin Manns
# Distributed under the terms of the GNU General Public License

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""

**Provides**

 * :class:`Entryline`

"""

from contextlib import contextmanager

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QTextOption, QKeyEvent
from PyQt5.QtWidgets import QWidget, QMainWindow

try:
    import pyspread.commands as commands
    from pyspread.lib.spelltextedit import SpellTextEdit
    from pyspread.lib.string_helpers import quote
except ImportError:
    import commands
    from lib.spelltextedit import SpellTextEdit
    from lib.string_helpers import quote


class Entryline(SpellTextEdit):
    """The entry line for pyspread"""

    def __init__(self, main_window: QMainWindow):
        """

        :param main_window: Application main window

        """

        super().__init__(line_numbers=False)

        self.main_window = main_window

        min_height = self.cursorRect().y() + self.cursorRect().height() + 20
        self.setMinimumHeight(min_height)

        self.setWordWrapMode(QTextOption.WrapAnywhere)

        self.installEventFilter(self)

        self.last_key = None

        # self.highlighter.setDocument(self.document())

    # Overrides

    def eventFilter(self, source: QWidget, event: QEvent):
        """Quotes editor content for <Ctrl>+<Enter> and <Ctrl>+<Return>

        Overrides SpellTextEdit default shortcut. Counts as undoable action.

        :param source: Source widget of event
        :param event: Event to be filtered

        """

        if event.type() == QEvent.ShortcutOverride \
           and event.modifiers() == Qt.ControlModifier \
           and source == self \
           and event.key() in (Qt.Key_Return, Qt.Key_Enter):

            code = quote(source.toPlainText())
            index = self.main_window.grid.currentIndex()
            description = "Quote code for cell {}".format(index)
            cmd = commands.SetCellCode(code, self.main_window.grid.model,
                                       index, description)
            self.main_window.undo_stack.push(cmd)

        return QWidget.eventFilter(self, source, event)

    @contextmanager
    def disable_highlighter(self):
        """Disables highlighter"""

        doc = self.highlighter.document()
        self.highlighter.setDocument(None)
        yield
        self.highlighter.setDocument(doc)

    def keyPressEvent(self, event: QKeyEvent):
        """Key press event filter

        :param event: Key event

        """

        self.last_key = event.key()

        if self.last_key in (Qt.Key_Enter, Qt.Key_Return) \
           and not event.modifiers() == Qt.ShiftModifier:
            self.store_data()
            self.main_window.grid.row += 1
        elif self.last_key == Qt.Key_Tab:
            self.store_data()
            self.main_window.grid.column += 1
        elif self.last_key == Qt.Key_Insert:
            self.main_window.grid.selection_mode = \
                not self.main_window.grid.selection_mode
        else:
            super().keyPressEvent(event)

    def store_data(self):
        """Stores current entry line data in grid model"""

        index = self.main_window.grid.currentIndex()
        model = self.main_window.grid.model

        description = "Set code for cell {}".format(index)
        command = commands.SetCellCode(self.toPlainText(), model, index,
                                       description)
        self.main_window.undo_stack.push(command)

    def on_toggle_spell_check(self, signal: bool):
        """Spell check toggle event handler

        :param signal: Spell check is enabled if True

        """

        self.highlighter.enable_enchant = bool(signal)

    def setPlainText(self, text: str):
        """Overides setPlainText

        Additionally shows busy cursor and disables highlighter on long texts,
        and omits identical replace.

        :param text: Text to be set

        """

        is_long = (text is not None
                   and len(text) > self.main_window.settings.highlighter_limit)

        if text == self.toPlainText():
            return

        if is_long:
            with self.main_window.workflows.busy_cursor():
                self.highlighter.setDocument(None)
                super().setPlainText(text)
        else:
            super().setPlainText(text)
