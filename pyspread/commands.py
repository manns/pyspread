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

**Provides**

* :class:`SetGridSize`
* :class:`SetCellCode`
* :class:`SetCellFormat`
* :class:`SetCellMerge`
* :class:`SetCellRenderer`
* :class:`SetCellTextAlignment`
* :class:`SetColumnWidth`
* :class:`SetRowHeight`


"""

from copy import copy
from typing import List, Iterable, Tuple

from PyQt5.QtCore import Qt, QModelIndex, QAbstractTableModel
from PyQt5.QtGui import QTextDocument
from PyQt5.QtWidgets import QUndoCommand, QTableView, QPlainTextEdit

try:
    from pyspread.model.model import CellAttribute
    from pyspread.widgets import CellButton

    from pyspread.lib.attrdict import AttrDict
    from pyspread.lib.selection import Selection
except ImportError:
    from model.model import CellAttribute
    from widgets import CellButton

    from lib.attrdict import AttrDict
    from lib.selection import Selection


class SetGridSize(QUndoCommand):
    """Sets size of grid"""

    def __init__(self, grid: QTableView, old_shape: Tuple[int, int, int],
                 new_shape: Tuple[int, int, int], description: str):
        """
        :param grid: The main grid object
        :param old_shape: Shape of the grid before command
        :param new_shape: Shape of the grid to be set
        :param description: Command description

        """

        super().__init__(description)

        self.grid = grid
        self.old_shape = old_shape
        self.new_shape = new_shape

        self.deleted_cells = {}  # Storage dict for deleted cells

    def redo(self):
        """Redo grid size change and deletion of cell code outside new shape

        Cell formats are not deleted.

        """

        model = self.grid.model
        code_array = model.code_array

        rows, columns, tables = self.new_shape
        shapeselection = Selection([(0, 0)], [(rows-1, columns-1)], [], [], [])

        for row, column, table in code_array.keys():
            if not (table < tables and (row, column) in shapeselection):
                # Code outside grid shape. Delete it and store cell data
                key = row, column, table
                self.deleted_cells[key] = code_array.pop(key)

        # Now change the shape
        self.grid.model.shape = self.new_shape

    def undo(self):
        """Undo grid size change and deletion of cell code outside new shape

        Cell formats are not deleted.

        """
        model = self.grid.model

        model.shape = self.old_shape

        for row, column, table in self.deleted_cells:
            index = model.index(row, column, QModelIndex())
            code = self.deleted_cells[(row, column, table)]
            model.setData(index, code, Qt.EditRole, raw=True, table=table)


class SetCellCode(QUndoCommand):
    """Sets cell code in grid"""

    def __init__(self, code: str, model: QAbstractTableModel,
                 index: QModelIndex, description: str):
        """
        :param code: The main grid object
        :param model: Model of the grid object
        :param index: Index of the cell for which the code is set
        :param description: Command description

        """
        super().__init__(description)

        self.description = description
        self.model = model
        self.indices = [index]
        self.old_codes = [model.code(index)]
        self.new_codes = [code]

    def id(self):
        return 1  # Enable command merging

    def mergeWith(self, other: QUndoCommand) -> bool:
        """Consecutive commands are merged if descriptions match

        :param other: Command to be merged

        """

        if self.description != other.description:
            return False
        self.new_codes += other.new_codes
        self.old_codes += other.old_codes
        self.indices += other.indices
        return True

    def redo(self):
        """Redo cell code setting

        During update, cell highlighting is disabled.

        """

        with self.model.main_window.entry_line.disable_highlighter():
            for index, new_code in zip(self.indices, self.new_codes):
                self.model.setData(index, new_code, Qt.EditRole, raw=True)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        """Undo cell code setting.

        During update, cell highlighting is disabled.

        """

        with self.model.main_window.entry_line.disable_highlighter():
            for index, old_code in zip(self.indices, self.old_codes):
                self.model.setData(index, old_code, Qt.EditRole, raw=True)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class SetRowsHeight(QUndoCommand):
    """Sets rows height in grid"""

    def __init__(self, grid: QTableView, rows: List[int], table: int,
                 old_height: float, new_height: float, description: str):
        """
        :param grid: The main grid object
        :param rows: Rows for which height are set
        :param table: Table for which row heights are set
        :param old_height: Row height before setting
        :param new_height: Target row height for setting
        :param description: Command description

        """

        super().__init__(description)

        self.grid = grid
        self.rows = rows
        self.table = table
        self.old_height = old_height
        self.new_height = new_height

        self.default_size = self.grid.verticalHeader().defaultSectionSize()

    def id(self) -> int:
        """Command id that enables command merging"""

        return 2

    def mergeWith(self, other: QUndoCommand) -> bool:
        """Consecutive commands are merged if descriptions match

        :param other: Command to be merged

        """

        if self.rows != other.rows:
            return False
        self.new_height = other.new_height
        return True

    def redo(self):
        """Redo row height setting"""

        for row in self.rows:
            if self.new_height != self.default_size:
                self.grid.model.code_array.row_heights[(row, self.table)] = \
                    self.new_height / self.grid.zoom
            if self.grid.rowHeight(row) != self.new_height:
                with self.grid.undo_resizing_row():
                    self.grid.setRowHeight(row, self.new_height)

    def undo(self):
        """Undo row height setting"""

        for row in self.rows:
            if self.old_height == self.default_size:
                self.grid.model.code_array.row_heights.pop((row, self.table))
            else:
                self.grid.model.code_array.row_heights[(row, self.table)] = \
                    self.old_height / self.grid.zoom
            if self.grid.rowHeight(row) != self.old_height:
                with self.grid.undo_resizing_row():
                    self.grid.setRowHeight(row, self.old_height)


class SetColumnsWidth(QUndoCommand):
    """Sets column width in grid"""

    def __init__(self, grid: QTableView, columns: List[int], table: int,
                 old_width: float, new_width: float, description: str):
        """
        :param grid: The main grid object
        :param columns: Columns for which widths are set
        :param table: Table for which column widths are set
        :param old_width: Column width before setting
        :param new_width: Target column width for setting
        :param description: Command description

        """

        super().__init__(description)

        self.grid = grid
        self.columns = columns
        self.table = table
        self.old_width = old_width
        self.new_width = new_width

        self.default_size = self.grid.horizontalHeader().defaultSectionSize()

    def id(self) -> int:
        """Command id that enables command merging"""

        return 3  # Enable command merging

    def mergeWith(self, other: QUndoCommand) -> bool:
        """Consecutive commands are merged if descriptions match

        :param other: Command to be merged

        """

        if self.columns != other.columns:
            return False
        self.new_width = other.new_width
        return True

    def redo(self):
        """Redo column width setting"""

        for column in self.columns:
            if self.new_width != self.default_size:
                self.grid.model.code_array.col_widths[(column, self.table)] =\
                    self.new_width / self.grid.zoom
            if self.grid.columnWidth(column) != self.new_width:
                with self.grid.undo_resizing_column():
                    self.grid.setColumnWidth(column, self.new_width)

    def undo(self):
        """Undo column width setting"""

        for column in self.columns:
            if self.old_width == self.default_size:
                self.grid.model.code_array.col_widths.pop((column, self.table))
            else:
                self.grid.model.code_array.col_widths[(column, self.table)] =\
                    self.old_width / self.grid.zoom
            if self.grid.columnWidth(column) != self.old_width:
                with self.grid.undo_resizing_column():
                    self.grid.setColumnWidth(column, self.old_width)


class InsertRows(QUndoCommand):
    """Inserts grid rows"""

    def __init__(self, grid: QTableView, model: QAbstractTableModel,
                 index: QModelIndex, row: int, count: int, description: str):
        """
        :param grid: The main grid object
        :param model: Model of the grid object
        :param index: Parent into which the new rows are inserted
        :param row: Row number that first row will have after insertion
        :param count: Number of rows to be inserted
        :param description: Command description

        """

        super().__init__(description)
        self.grid = grid
        self.model = model
        self.index = index
        self.first = self.row = row
        self.last = row + count
        self.count = count

    def redo(self):
        """Redo row insertion, updates screen"""

        # Store content of overflowing rows
        self.old_row_heights = copy(self.model.code_array.row_heights)
        self.old_cell_attributes = copy(self.model.code_array.cell_attributes)
        self.old_code = {}

        no_rows = self.model.shape[0]
        rows = list(range(no_rows-self.count, no_rows+1))
        selection = Selection([], [], rows, [], [])
        for key in selection.cell_generator(self.model.shape, self.grid.table):
            old_code = self.model.code_array(key)
            if old_code is not None:
                self.old_code[key] = old_code

        with self.model.inserting_rows(self.index, self.first, self.last):
            self.model.insertRows(self.row, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        """Undo row insertion, updates screen"""

        # Clear must be first so that merged cells do not consume values
        self.model.code_array.dict_grid.cell_attributes.clear()

        with self.model.removing_rows(self.index, self.first, self.last):
            self.model.removeRows(self.row, self.count)

        self.model.code_array.dict_grid.row_heights = self.old_row_heights

        for ca in self.old_cell_attributes:
            self.model.code_array.dict_grid.cell_attributes.append(ca)

        for key in self.old_code:
            self.model.code_array[key] = self.old_code[key]
        self.grid.table_choice.on_table_changed(self.grid.current)


class DeleteRows(QUndoCommand):
    """Deletes grid rows"""

    def __init__(self, grid: QTableView, model: QAbstractTableModel,
                 index: QModelIndex, row: int, count: int, description: str):
        """
        :param grid: The main grid object
        :param model: Model of the grid object
        :param index: Parent from which the new rows are deleted
        :param row: Row number of the first row to be deleted
        :param count: Number of rows to be deleted
        :param description: Command description

        """

        super().__init__(description)
        self.grid = grid
        self.model = model
        self.index = index
        self.first = self.row = row
        self.last = row + count
        self.count = count

    def redo(self):
        """Redo row deletion, updates screen"""

        # Store content of deleted rows
        self.old_row_heights = copy(self.model.code_array.row_heights)
        self.old_cell_attributes = copy(self.model.code_array.cell_attributes)
        self.old_code = {}
        rows = list(range(self.first, self.last+1))
        selection = Selection([], [], rows, [], [])
        for key in selection.cell_generator(self.model.shape, self.grid.table):
            self.old_code[key] = self.model.code_array(key)

        with self.model.removing_rows(self.index, self.first, self.last):
            self.model.removeRows(self.row, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        """Undo row deletion, updates screen"""

        # Clear must be first so that merged cells do not consume values
        self.model.code_array.dict_grid.cell_attributes.clear()

        with self.model.inserting_rows(self.index, self.first, self.last):
            self.model.insertRows(self.row, self.count)

        self.model.code_array.dict_grid.row_heights = self.old_row_heights

        for ca in self.old_cell_attributes:
            self.model.code_array.dict_grid.cell_attributes.append(ca)
        for key in self.old_code:
            self.model.code_array[key] = self.old_code[key]

        self.grid.table_choice.on_table_changed(self.grid.current)


class InsertColumns(QUndoCommand):
    """Inserts grid columns"""

    def __init__(self, grid: QTableView, model: QAbstractTableModel,
                 index: QModelIndex, column: int, count: int,
                 description: str):
        """
        :param grid: The main grid object
        :param model: Model of the grid object
        :param index: Parent into which the new columns are inserted
        :param column: Column number of the first column after insertion
        :param count: Number of columns to be inserted
        :param description: Command description

        """

        super().__init__(description)
        self.grid = grid
        self.model = model
        self.index = index
        self.column = column
        self.first = self.column = column
        self.last = column + count
        self.count = count

    def redo(self):
        """Redo column insertion, updates screen"""

        # Store content of overflowing columns
        self.old_col_widths = copy(self.model.code_array.col_widths)
        self.old_cell_attributes = copy(self.model.code_array.cell_attributes)
        self.old_code = {}
        no_columns = self.model.shape[1]
        columns = list(range(no_columns-self.count, no_columns+1))
        selection = Selection([], [], [], columns, [])
        for key in selection.cell_generator(self.model.shape, self.grid.table):
            old_code = self.model.code_array(key)
            if old_code is not None:
                self.old_code[key] = old_code

        with self.model.inserting_columns(self.index, self.first, self.last):
            self.model.insertColumns(self.column, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        """Undo column insertion, updates screen"""

        # Clear must be first so that merged cells do not consume values
        self.model.code_array.dict_grid.cell_attributes.clear()

        with self.model.removing_rows(self.index, self.first, self.last):
            self.model.removeColumns(self.column, self.count)

        self.model.code_array.dict_grid.col_widths = self.old_col_widths

        for ca in self.old_cell_attributes:
            self.model.code_array.dict_grid.cell_attributes.append(ca)
        for key in self.old_code:
            self.model.code_array[key] = self.old_code[key]

        self.grid.table_choice.on_table_changed(self.grid.current)


class DeleteColumns(QUndoCommand):
    """Deletes grid columns"""

    def __init__(self, grid: QTableView, model: QAbstractTableModel,
                 index: QModelIndex, column: int, count: int,
                 description: str):
        """
        :param grid: The main grid object
        :param model: Model of the grid object
        :param index: Parent from which the new columns are deleted
        :param column: Column number of the first column to be deleted
        :param count: Number of columns to be deleted
        :param description: Command description

        """

        super().__init__(description)
        self.grid = grid
        self.model = model
        self.index = index
        self.column = column
        self.first = self.column = column
        self.last = column + count
        self.count = count

    def redo(self):
        """Redo column deletion, updates screen"""

        # Store content of deleted columns
        self.old_col_widths = copy(self.model.code_array.col_widths)
        self.old_cell_attributes = copy(self.model.code_array.cell_attributes)
        self.old_code = {}
        columns = list(range(self.first, self.last+1))
        selection = Selection([], [], [], columns, [])
        for key in selection.cell_generator(self.model.shape, self.grid.table):
            self.old_code[key] = self.model.code_array(key)

        with self.model.removing_columns(self.index, self.first, self.last):
            self.model.removeColumns(self.column, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        """Undo column deletion, updates screen"""

        # Clear must be first so that merged cells do not consume values
        self.model.code_array.dict_grid.cell_attributes.clear()

        with self.model.inserting_columns(self.index, self.first, self.last):
            self.model.insertColumns(self.column, self.count)

        self.model.code_array.dict_grid.col_widths = self.old_col_widths

        for ca in self.old_cell_attributes:
            self.model.code_array.dict_grid.cell_attributes.append(ca)
        for key in self.old_code:
            self.model.code_array[key] = self.old_code[key]

        self.grid.table_choice.on_table_changed(self.grid.current)


class InsertTable(QUndoCommand):
    """Inserts table"""

    def __init__(self, grid: QTableView, model: QAbstractTableModel,
                 table: int, description: str):
        """
        :param grid: The main grid object
        :param model: Model of the grid object
        :param table: Table number for insertion
        :param description: Command description

        """

        super().__init__(description)
        self.grid = grid
        self.model = model
        self.table = table

    def redo(self):
        """Redo table insertion, updates row and column sizes and screen"""

        # Store content of overflowing table
        self.old_row_heights = copy(self.model.code_array.row_heights)
        self.old_col_widths = copy(self.model.code_array.col_widths)
        self.old_cell_attributes = copy(self.model.code_array.cell_attributes)
        self.old_code = {}
        for key in self.model.code_array:
            if key[2] == self.model.shape[2] - 1:
                self.old_code[key] = self.model.code_array(key)

        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.model.insertTable(self.table)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        """Undo table insertion, updates row and column sizes and screen"""

        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.model.removeTable(self.table)

                self.model.code_array.dict_grid.row_heights = \
                    self.old_row_heights
                self.model.code_array.dict_grid.col_widths = \
                    self.old_col_widths
                self.model.code_array.dict_grid.cell_attributes.clear()
                for ca in self.old_cell_attributes:
                    self.model.code_array.dict_grid.cell_attributes.append(ca)
                for key in self.old_code:
                    self.model.code_array[key] = self.old_code[key]

        self.grid.table_choice.on_table_changed(self.grid.current)


class DeleteTable(QUndoCommand):
    """Deletes table"""

    def __init__(self, grid: QTableView, model: QAbstractTableModel,
                 table: int, description: str):
        """
        :param grid: The main grid object
        :param model: Model of the grid object
        :param table: Table number for deletion
        :param description: Command description

        """

        super().__init__(description)
        self.grid = grid
        self.model = model
        self.table = table

    def redo(self):
        """Redo table deletion, updates row and column sizes and screen"""

        # Store content of deleted table
        self.old_row_heights = copy(self.model.code_array.row_heights)
        self.old_col_widths = copy(self.model.code_array.col_widths)
        self.old_cell_attributes = copy(self.model.code_array.cell_attributes)
        self.old_code = {}
        for key in self.model.code_array:
            if key[2] == self.table:
                self.old_code[key] = self.model.code_array(key)

        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.model.removeTable(self.table)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        """Undo table deletion, updates row and column sizes and screen"""

        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.model.insertTable(self.table)

                self.model.code_array.dict_grid.row_heights = \
                    self.old_row_heights
                self.model.code_array.dict_grid.col_widths = \
                    self.old_col_widths
                self.model.code_array.dict_grid.cell_attributes.clear()
                for ca in self.old_cell_attributes:
                    self.model.code_array.dict_grid.cell_attributes.append(ca)
                for key in self.old_code:
                    self.model.code_array[key] = self.old_code[key]

        self.grid.table_choice.on_table_changed(self.grid.current)


class SetCellFormat(QUndoCommand):
    """Sets cell format in grid

    Format is set for one given cell and a selection.

    """

    def __init__(self, attr: CellAttribute, model: QAbstractTableModel,
                 index: QModelIndex, selected_idx: Iterable[QModelIndex],
                 description: str):
        """
        :param attr: Cell format to be set
        :param model: Model of the grid object
        :param index: Index of the cell for which the format is set
        :param selected_idx: Indexes of cells for which the format is set
        :param description: Command description

        """

        super().__init__(description)

        self.attr = attr
        self.model = model
        self.index = index
        self.selected_idx = selected_idx

    def redo(self):
        """Redo cell formatting"""

        self.model.setData(self.selected_idx, self.attr, Qt.DecorationRole)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        """Undo cell formatting"""

        self.model.code_array.cell_attributes.pop()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class SetCellMerge(SetCellFormat):
    """Sets cell merges in grid"""

    def redo(self):
        """Redo cell merging"""

        self.model.setData(self.selected_idx, self.attr, Qt.DecorationRole)
        self.model.main_window.grid.update_cell_spans()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        """Undo cell merging"""

        try:
            self.model.code_array.cell_attributes.pop()
        except IndexError as error:
            raise Warning(str(error))
            return
        self.model.main_window.grid.update_cell_spans()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class SetCellTextAlignment(SetCellFormat):
    """Sets cell text alignment in grid"""

    def redo(self):
        """Redo cell text alignment"""

        self.model.setData(self.selected_idx, self.attr, Qt.TextAlignmentRole)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class FreezeCell(QUndoCommand):
    """Freezes cell in grid"""

    def __init__(self, model: QAbstractTableModel,
                 current: Tuple[int, int, int], description: str):
        """
        :param model: Model of the grid object
        :param current: Index of the cell to be frozen
        :param description: Command description

        """

        super().__init__(description)

        self.model = model
        self.current = current

    def redo(self):
        """Redo cell freezing"""

        row, column, table = self.current

        # Add frozen cache content
        res_obj = self.model.code_array[self.current]
        self.model.code_array.frozen_cache[repr(self.current)] = res_obj

        # Set the frozen state
        selection = Selection([], [], [], [], [(row, column)])
        attr_dict = AttrDict([("frozen", True)])
        attr = CellAttribute(selection, table, attr_dict)
        self.model.setData([], attr, Qt.DecorationRole)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        """Undo cell freezing"""

        self.model.code_array.frozen_cache.pop(repr(self.current))
        self.model.code_array.cell_attributes.pop()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class ThawCell(FreezeCell):
    """Thaw (unfreezes) cell in grid"""

    def redo(self):
        """Redo cell thawing"""

        row, column, table = current = self.current

        # Remove and store frozen cache content
        self.res_obj = self.model.code_array.frozen_cache.pop(repr(current))

        # Remove the frozen state
        selection = Selection([], [], [], [], [(row, column)])
        attr_dict = AttrDict([("frozen", False)])
        attr = CellAttribute(selection, table, attr_dict)
        self.model.setData([], attr, Qt.DecorationRole)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        """Undo cell thawing"""

        self.model.code_array.frozen_cache[repr(self.current)] = self.res_obj
        self.model.code_array.cell_attributes.pop()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class SetCellRenderer(QUndoCommand):
    """Sets cell renderer in grid

    Adjusts syntax highlighting in entry line.

    """

    def __init__(self, attr: CellAttribute, model: QAbstractTableModel,
                 entry_line: QPlainTextEdit,
                 highlighter_document: QTextDocument,
                 index: QModelIndex, selected_idx: Iterable[QModelIndex],
                 description: str):
        """
        :param attr: Cell format that cointains traget renderer information
        :param model: Model of the grid object
        :param entry_line: Entry line in main window
        :param highlighter_document: Document for entry line
        :param index: Index of the cell for which the renderer is set
        :param selected_idx: Indexes of cells for which the renderer is set
        :param description: Command description

        """

        super().__init__(description)

        self.attr = attr
        self.description = description
        self.model = model
        self.entry_line = entry_line
        self.new_highlighter_document = highlighter_document
        self.old_highlighter_document = self.entry_line.highlighter.document()
        self.index = index
        self.selected_idx = selected_idx

    def redo(self):
        """Redo cell renderer setting, adjusts syntax highlighting"""

        self.model.setData(self.selected_idx, self.attr, Qt.DecorationRole)
        self.entry_line.highlighter.setDocument(self.new_highlighter_document)
        self.model.dataChanged.emit(self.index, self.index)

    def undo(self):
        """Undo cell renderer setting, adjusts syntax highlighting"""

        self.model.code_array.cell_attributes.pop()
        self.entry_line.highlighter.setDocument(self.old_highlighter_document)
        self.model.dataChanged.emit(self.index, self.index)


class MakeButtonCell(QUndoCommand):
    """Makes a button cell"""

    def __init__(self, grid: QTableView, text: str, index: QModelIndex,
                 description: str):
        """
        :param grid: Main grid object
        :param text: Button cell text
        :param index: Index of the cell which becomes a button cell
        :param description: Command description

        """

        super().__init__(description)
        self.grid = grid
        self.text = text
        self.index = index
        self.key = self.index.row(), self.index.column(), self.grid.table

    def redo(self):
        """Redo button cell making"""

        row, column, table = self.key
        selection = Selection([], [], [], [], [(row, column)])
        attr_dict = AttrDict([("button_cell", self.text)])
        ca = CellAttribute(selection, table, attr_dict)
        self.grid.model.setData([self.index], ca, Qt.DecorationRole)

        if table == self.grid.table:
            # Only add widget if we are in the right table
            button = CellButton(self.text, self.grid, self.key)
            self.grid.setIndexWidget(self.index, button)
            self.grid.widget_indices.append(self.index)

        self.grid.model.dataChanged.emit(self.index, self.index)

    def undo(self):
        """Undo button cell making"""

        if self.index not in self.grid.widget_indices:
            return

        row, column, table = self.key
        selection = Selection([], [], [], [], [(row, column)])
        attr_dict = AttrDict([("button_cell", False)])
        ca = CellAttribute(selection, table, attr_dict)
        self.grid.model.setData([self.index], ca, Qt.DecorationRole)

        if table == self.grid.table:
            # Only remove widget if we are in the right table
            self.grid.setIndexWidget(self.index, None)
            self.grid.widget_indices.remove(self.index)
        self.grid.model.dataChanged.emit(self.index, self.index)


class RemoveButtonCell(QUndoCommand):
    """Removes a button cell"""

    def __init__(self, grid: QTableView, index: QModelIndex, description: str):
        """
        :param grid: Main grid object
        :param index: Index of the cell where a button cell is removed
        :param description: Command description

        """

        super().__init__(description)
        self.grid = grid
        self.text = None
        self.index = index
        self.key = self.index.row(), self.index.column(), self.grid.table

    def redo(self):
        """Redo button cell removal"""

        if self.index not in self.grid.widget_indices:
            return
        attr = self.grid.model.code_array.cell_attributes[self.key]
        self.text = attr.button_cell
        row, column, table = self.key
        selection = Selection([], [], [], [], [(row, column)])
        attr_dict = AttrDict([("button_cell", False)])
        ca = CellAttribute(selection, table, attr_dict)
        self.grid.model.setData([self.index], ca, Qt.DecorationRole)

        if table == self.grid.table:
            # Only remove widget if we are in the right table
            self.grid.setIndexWidget(self.index, None)
            self.grid.widget_indices.remove(self.index)
        self.grid.model.dataChanged.emit(self.index, self.index)

    def undo(self):
        """Undo button cell removal"""

        row, column, table = self.key
        selection = Selection([], [], [], [], [(row, column)])
        attr_dict = AttrDict([("button_cell", self.text)])
        ca = CellAttribute(selection, table, attr_dict)
        self.grid.model.setData([self.index], ca, Qt.DecorationRole)

        if table == self.grid.table:
            # Only add widget if we are in the right table
            button = CellButton(self.text, self.grid, self.key)
            self.grid.setIndexWidget(self.index, button)
            self.grid.widget_indices.append(self.index)
        self.grid.model.dataChanged.emit(self.index, self.index)
