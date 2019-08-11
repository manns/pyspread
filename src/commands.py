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
    """Sets cell code in grid"""

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


class CommandSetCellFormat(QUndoCommand):
    """Sets cell format in grid"""

    def __init__(self, attr, model, index, selected_idx, description):
        super().__init__(description)

        self.attr = attr
        self.model = model
        self.index = index
        self.selected_idx = selected_idx

    def redo(self):
        self.model.setData(self.selected_idx, self.attr, Qt.DecorationRole)
        self.model.dataChanged.emit(self.index, self.index)

    def undo(self):
        self.model.code_array.cell_attributes.pop()
        self.model.dataChanged.emit(self.index, self.index)


class CommandSetCellRenderer(QUndoCommand):
    """Sets cell renderer in grid"""

    def __init__(self, attr, model, entry_line, highlighter_document,
                 index, selected_idx, description):
        super().__init__(description)

        self.attr = attr
        self.model = model
        self.entry_line = entry_line
        self.new_highlighter_document = highlighter_document
        self.old_highlighter_document = self.entry_line.highlighter.document()
        self.index = index
        self.selected_idx = selected_idx

    def redo(self):
        self.model.setData(self.selected_idx, self.attr, Qt.DecorationRole)
        self.entry_line.highlighter.setDocument(self.new_highlighter_document)
        self.model.dataChanged.emit(self.index, self.index)

    def undo(self):
        self.model.code_array.cell_attributes.pop()
        self.entry_line.highlighter.setDocument(self.old_highlighter_document)
        self.model.dataChanged.emit(self.index, self.index)
