#!/usr/bin/env python3
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
Pyspread undoable commands
--------------------------

"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QUndoCommand


class CommandSetCellCode(QUndoCommand):
    """Stores cell code in grid"""

    def __init__(self, code, model, index, description):
        super().__init__(description)

        self.model = model
        self.index = index
        self.old_code = model.code(index)
        self.new_code = code

    def redo(self):
        self.model.setData(self.index, self.new_code, Qt.EditRole, raw=True)

    def undo(self):
        self.model.setData(self.index, self.old_code, Qt.EditRole, raw=True)
