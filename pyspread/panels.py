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

 * :class:`MacroPanel`

"""

import ast
from io import StringIO
from sys import exc_info
from traceback import print_exception

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QSplitter
from PyQt5.QtWidgets import QTextEdit

try:
    from pyspread.lib.spelltextedit import SpellTextEdit
    from pyspread.lib.exception_handling import get_user_codeframe
except ImportError:
    from lib.spelltextedit import SpellTextEdit
    from lib.exception_handling import get_user_codeframe


class MacroPanel(QDialog):
    """The macro panel"""

    def __init__(self, parent, code_array):
        super().__init__()

        self.parent = parent
        self.code_array = code_array

        self._init_widgets()
        self._layout()

        self.update()

        self.default_text_color = self.result_viewer.textColor()
        self.error_text_color = QColor("red")

        self.button_box.clicked.connect(self.on_apply)

    def _init_widgets(self):
        """Inititialize widgets"""

        self.macro_editor = SpellTextEdit(self)

        self.result_viewer = QTextEdit(self)
        self.result_viewer.setReadOnly(True)

        self.splitter = QSplitter(Qt.Vertical, self)

        self.splitter.addWidget(self.macro_editor)
        self.splitter.addWidget(self.result_viewer)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Apply)

    def _layout(self):
        """Layout dialog widgets"""

        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def _is_invalid_code(self) -> str:
        """Preliminary code check

        Returns a string with the error message if code is not valid Python.
        If the code runs without errors, an empty string is retruned.

        """

        try:
            ast.parse(self.code_array.macros)

        except Exception:
            # Grab the traceback and return it
            stringio = StringIO()
            excinfo = exc_info()
            # usr_tb will more than likely be none because ast throws
            # SytnaxErrors as occurring outside of the current execution frame
            usr_tb = get_user_codeframe(excinfo[2]) or None
            print_exception(excinfo[0], excinfo[1], usr_tb, None, stringio)
            return stringio.getvalue()
        else:
            return ''

    def on_apply(self):
        """Event handler for Apply button"""

        self.code_array.macros = self.macro_editor.toPlainText()

        err = self._is_invalid_code()
        if err:
            self.update_result_viewer(err=err)
        else:
            self.update_result_viewer(*self.code_array.execute_macros())

        self.parent.grid.gui_update()

    def update(self):
        """Update macro content"""

        self.macro_editor.setPlainText(self.code_array.macros)
        self.on_apply()

    def update_result_viewer(self, result: str = "", err: str = ""):
        """Update event result following execution by main window

        :param result: Text to be shown in the result viewer in default color
        :param err: Text to be shown in the result viewer in error text color

        """

        self.result_viewer.clear()

        if result:
            self.result_viewer.append(result)
        if err:
            self.result_viewer.setTextColor(self.error_text_color)
            self.result_viewer.append(err)
            self.result_viewer.setTextColor(self.default_text_color)
