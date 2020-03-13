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


The model contains the core data structures of pyspread and is divided
into the following layers.

- Layer 3: :class:`CodeArray`
- Layer 2: :class:`DataArray`
- Layer 1: :class:`DictGrid`
- Layer 0: :class:`KeyValueStore`

"""
from __future__ import absolute_import
from builtins import filter
from builtins import str
from builtins import zip
from builtins import range
from builtins import object

import ast
import base64
import bz2
from copy import copy
import datetime
from inspect import isgenerator
from itertools import product
import re
import sys

import numpy
from PyQt5.QtGui import QImage, QPixmap

import lib.charts as charts
from lib.typechecks import isslice, isstring
from lib.selection import Selection


class CellAttributes(list):
    """Stores cell formatting attributes in a list of three tuples

    - The first element of each tuple is a Selection.
    - The second element is the table
    - The third element is a `dict` of attributes that are altered.

    The class provides attribute read access to single cells via
    :meth:`__getitem__`.
    Otherwise it behaves similar to a `list`.

    """

    def __init__(self, *args, **kwargs):
        self.__add__ = None
        self.__delattr__ = None
        self.__delitem__ = None
        self.__delslice__ = None
        self.__iadd__ = None
        self.__imul__ = None
        self.__rmul__ = None
        self.__setattr__ = None
        self.__setslice__ = None
        self.insert = None
        self.remove = None
        self.reverse = None
        self.sort = None

    default_cell_attributes = {
        "borderwidth_bottom": 1,
        "borderwidth_right": 1,
        "bordercolor_bottom": None,
        "bordercolor_right": None,
        "bgcolor": None,
        "textfont": None,
        "pointsize": 10,
        "fontweight": None,
        "fontstyle": None,
        "textcolor": None,
        "underline": False,
        "strikethrough": False,
        "locked": False,
        "angle": 0.0,
        "column-width": 75,
        "row-height": 26,
        "vertical_align": "align_top",
        "justification": "justify_left",
        "frozen": False,
        "merge_area": None,
        "renderer": "text",
        "button_cell": False,
        "panel_cell": False,
    }

    # Cache for __getattr__ maps key to tuple of len and attr_dict

    _attr_cache = {}
    _table_cache = {}

    def append(self, value):
        """append that clears caches"""

        # We need to clean up merge areas
        selection, table, attr = value
        if "merge_area" in attr:
            for i, ele in enumerate(reversed(self)):
                if ele[0] == selection and ele[1] == table \
                   and "merge_area" in ele[2]:
                    self.pop(-1 - i)
            if attr["merge_area"] is not None:
                super().append(value)
        else:
            super().append(value)

        self._attr_cache.clear()
        self._table_cache.clear()

    def __getitem__(self, key):
        """Returns attribute dict for a single key"""

        assert not any(type(key_ele) is slice for key_ele in key)

        if key in self._attr_cache:
            cache_len, cache_dict = self._attr_cache[key]

            # Use cache result only if no new attrs have been defined
            if cache_len == len(self):
                return cache_dict

        # Update table cache if it is outdated (e.g. when creating a new grid)
        if len(self) != self._len_table_cache():
            self._update_table_cache()

        row, col, tab = key

        result_dict = copy(self.default_cell_attributes)

        try:
            for selection, attr_dict in self._table_cache[tab]:
                if (row, col) in selection:
                    result_dict.update(attr_dict)
        except KeyError:
            pass

        # Upddate cache with current length and dict
        self._attr_cache[key] = (len(self), result_dict)

        return result_dict

    def __setitem__(self, key, value):
        """__setitem__ that clears caches"""

        super().__setitem__(key, value)

        self._attr_cache.clear()
        self._table_cache.clear()

    def _len_table_cache(self):
        """Returns the length of the table cache"""

        length = 0

        for table in self._table_cache:
            length += len(self._table_cache[table])

        return length

    def _update_table_cache(self):
        """Clears and updates the table cache to be in sync with self"""

        self._table_cache.clear()
        for sel, tab, val in self:
            try:
                self._table_cache[tab].append((sel, val))
            except KeyError:
                self._table_cache[tab] = [(sel, val)]

        assert len(self) == self._len_table_cache()

    def get_merging_cell(self, key):
        """Returns key of cell that merges the cell key

        or None if cell key not merged

        :param key: Key of the cell that is merged
        :type key: tuple

        """

        row, col, tab = key

        # Is cell merged
        for selection, table, attr in self:
            if tab == table and "merge_area" in attr:
                top, left, bottom, right = attr["merge_area"]
                if top <= row <= bottom and left <= col <= right:
                    return top, left, tab

    def for_table(self, table):
        """Return cell attributes for a given table"""

        # table presence in grid is not checked

        table_cell_attributes = CellAttributes()

        for selection, __table, attr in self:
            if __table == table:
                table_cell_attributes.append((selection, __table, attr))

        return table_cell_attributes

# End of class CellAttributes


class KeyValueStore(dict):
    """Key-Value store in memory. Currently a dict with default value None.

    This class represents layer 0 of the model.

    """

    def __init__(self, default_value=None):
        super().__init__()
        self.default_value = default_value

    def __missing__(self, value):
        """Returns the default value None"""

        return self.default_value

# End of class KeyValueStore

# -----------------------------------------------------------------------------


class DictGrid(KeyValueStore):
    """Core data class with all information that is stored in a `.pys` file.

    Besides grid code access via standard `dict` operations, it provides
    the following attributes:

    * :attr:`~DictGrid.cell_attributes` -  Stores cell formatting attributes
    * :attr:`~DictGrid.macros` - String of all macros

    This class represents layer 1 of the model.

    :param shape: Shape of the grid
    :type shape: tuple

    """

    def __init__(self, shape):
        super().__init__()

        self.shape = shape

        self.cell_attributes = CellAttributes()
        """Instance of :class:`CellAttributes`"""

        self.macros = u""
        """Macros as string"""

        # We need to import this here for the unit tests to work
        from collections import defaultdict

        self.row_heights = defaultdict(float)  # Keys have format (row, table)
        self.col_widths = defaultdict(float)  # Keys have format (col, table)

    def __getitem__(self, key):

        shape = self.shape

        for axis, key_ele in enumerate(key):
            if shape[axis] <= key_ele or key_ele < -shape[axis]:
                msg = "Grid index {key} outside grid shape {shape}."
                msg = msg.format(key=key, shape=shape)
                raise IndexError(msg)

        return super().__getitem__(key)

    def __missing__(self, key):
        """Default value is None"""

        return

# End of class DictGrid

# -----------------------------------------------------------------------------


class DataArray:
    """DataArray provides enhanced grid read/write access.

    Enhancements comprise:
     * Slicing
     * Multi-dimensional operations such as insertion and deletion along one
       axis

    This class represents layer 2 of the model.

    :param shape: Shape of the grid
    :type shape: tuple

    """

    def __init__(self, shape, settings):
        self.dict_grid = DictGrid(shape)
        self.settings = settings

        # Safe mode
        self.safe_mode = False
        """Whether pyspread is operating in safe_mode

        .. todo:: Explain safe mode
        """

    def __eq__(self, other):
        if not hasattr(other, "dict_grid") or \
           not hasattr(other, "cell_attributes"):
            return False

        return self.dict_grid == other.dict_grid and \
            self.cell_attributes == other.cell_attributes

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def data(self):
        """Returns `dict` of data content.


        - Data is the central content interface for loading / saving data.
        - It shall be used for loading and saving from and to `.pys` and other
          files.
        - It shall be used for loading and saving macros.
        - However, it is not used for importing and exporting data because
          these operations are partial to the grid.

        Keys:

        shape: 3-tuple of Integer
        \tGrid shape
        grid: Dict of 3-tuples to strings
        \tCell content
        attributes: List of 3-tuples
        \tCell attributes
        row_heights: Dict of 2-tuples to float
        \t(row, tab): row_height
        col_widths: Dict of 2-tuples to float
        \t(col, tab): col_width
        macros: String
        \tMacros from macro list

        """

        data = {}

        data["shape"] = self.shape
        data["grid"] = {}.update(self.dict_grid)
        data["attributes"] = [ca for ca in self.cell_attributes]
        data["row_heights"] = self.row_heights
        data["col_widths"] = self.col_widths
        data["macros"] = self.macros

        return data

    @data.setter
    def data(self, **kwargs):
        """Sets data from given parameters

        Old values are deleted.
        If a paremeter is not given, nothing is changed.

        :param shape: Grid shape
        :type shape: tuple
        :param grid: Cell content
        :type grid: dict
        :param attributes: Cell attributes
        :type attributes: CellAttributes
        :param row_heights: Dict (row, tab): row_height
        :type row_heights: dict
        :param col_widths: Dict (col, tab): col_width
        :type col_widths: dict
        :param macros: Macros from macro list
        :type macros: str

        """

        if "shape" in kwargs:
            self.shape = kwargs["shape"]

        if "grid" in kwargs:
            self.dict_grid.clear()
            self.dict_grid.update(kwargs["grid"])

        if "attributes" in kwargs:
            self.attributes[:] = kwargs["attributes"]

        if "row_heights" in kwargs:
            self.row_heights = kwargs["row_heights"]

        if "col_widths" in kwargs:
            self.col_widths = kwargs["col_widths"]

        if "macros" in kwargs:
            self.macros = kwargs["macros"]

    @property
    def row_heights(self):
        """row_heights interface to dict_grid"""

        return self.dict_grid.row_heights

    @row_heights.setter
    def _row_heights(self, row_heights):
        """row_heights interface to dict_grid"""

        self.dict_grid.row_heights = row_heights

    @property
    def col_widths(self):
        """col_widths interface to dict_grid"""

        return self.dict_grid.col_widths

    @col_widths.setter
    def col_widths(self, col_widths):
        """col_widths interface to dict_grid"""

        self.dict_grid.col_widths = col_widths

    @property
    def cell_attributes(self):
        """cell_attributes interface to dict_grid"""

        return self.dict_grid.cell_attributes

    @cell_attributes.setter
    def cell_attributes(self, value):
        """cell_attributes interface to dict_grid"""

        # First empty cell_attributes
        self.cell_attributes[:] = []
        self.cell_attributes.extend(value)

    @property
    def macros(self):
        """macros interface to dict_grid"""

        return self.dict_grid.macros

    @macros.setter
    def macros(self, macros):
        """Sets  macros string"""

        self.dict_grid.macros = macros

    @property
    def shape(self):
        """Returns dict_grid shape"""

        return self.dict_grid.shape

    @shape.setter
    def shape(self, shape):
        """Deletes all cells beyond new shape and sets dict_grid shape

        Returns a dict of the deleted cells' contents

        :param shape: Target shape for grid
        :type shape: tuple

        """

        # Delete each cell that is beyond new borders

        old_shape = self.shape
        deleted_cells = {}

        if any(new_axis < old_axis
               for new_axis, old_axis in zip(shape, old_shape)):
            for key in list(self.dict_grid.keys()):
                if any(key_ele >= new_axis
                       for key_ele, new_axis in zip(key, shape)):
                    deleted_cells[key] = self.pop(key)

        # Set dict_grid shape attribute
        self.dict_grid.shape = shape

        self._adjust_rowcol(0, 0, 0)
        self._adjust_cell_attributes(0, 0, 0)

        return deleted_cells

    def __iter__(self):
        """Returns iterator over self.dict_grid"""

        return iter(self.dict_grid)

    def __contains__(self, key):
        """Handles single keys only"""

        if any(not isinstance(ele, int) for ele in key):
            return NotImplemented

        row, column, table = key
        rows, columns, tables = self.shape

        return (0 <= row <= rows
                and 0 <= column <= columns
                and 0 <= table <= tables)

    # Slice support

    def __getitem__(self, key):
        """Adds slicing access to cell code retrieval

        The cells are returned as a generator of generators, of ... of unicode.

        :param key: Keys of the cell code that is returned
        :type key:  tuple of integer or slice

        Note
        ----
        Classical Excel type addressing (A$1, ...) may be added here

        """

        for key_ele in key:
            if isslice(key_ele):
                # We have something slice-like here

                return self.cell_array_generator(key)

            elif isstring(key_ele):
                # We have something string-like here
                msg = "Cell string based access not implemented"
                raise NotImplementedError(msg)

        # key_ele should be a single cell

        return self.dict_grid[key]

    def __setitem__(self, key, value):
        """Accepts index and slice keys

        :param key: Cell key(s) that shall be set
        :type key: tuple of 3 int or 3 slice
        :param value: Code for cell(s) to be set
        :type value: str

        """

        single_keys_per_dim = []

        for axis, key_ele in enumerate(key):
            if isslice(key_ele):
                # We have something slice-like here

                length = key[axis]
                slice_range = range(*key_ele.indices(length))
                single_keys_per_dim.append(slice_range)

            elif isstring(key_ele):
                # We have something string-like here

                raise NotImplementedError

            else:
                # key_ele is a single cell

                single_keys_per_dim.append((key_ele, ))

        single_keys = product(*single_keys_per_dim)

        for single_key in single_keys:
            if value:
                # Never change merged cells
                merging_cell = \
                    self.cell_attributes.get_merging_cell(single_key)
                if merging_cell is None or merging_cell == single_key:
                    self.dict_grid[single_key] = value
            else:
                # Value is empty --> delete cell
                try:
                    self.pop(key)

                except (KeyError, TypeError):
                    pass

    # Pickle support

    def __getstate__(self):
        """Returns dict_grid for pickling

        Note that all persistent data is contained in the DictGrid class

        """

        return {"dict_grid": self.dict_grid}

    def get_row_height(self, row, tab):
        """Returns row height"""

        try:
            return self.row_heights[(row, tab)]

        except KeyError:
            return

    def get_col_width(self, col, tab):
        """Returns column width"""

        try:
            return self.col_widths[(col, tab)]

        except KeyError:
            return

    def keys(self):
        """Returns keys in self.dict_grid"""

        return list(self.dict_grid.keys())

    def pop(self, key):
        """dict_grid pop wrapper"""

        return self.dict_grid.pop(key)

    def get_last_filled_cell(self, table=None):
        """Returns key for the bottommost rightmost cell with content

        :param table: Limit search to this table
        :type table: int, optional

        """

        maxrow = 0
        maxcol = 0

        for row, col, tab in self.dict_grid:
            if table is None or tab == table:
                maxrow = max(row, maxrow)
                maxcol = max(col, maxcol)

        return maxrow, maxcol, table

    def cell_array_generator(self, key):
        """Generator traversing cells specified in key

        :param key: Specifies the cell keys of the generator
        :type key: Iterable of Integer or slice

        """

        for i, key_ele in enumerate(key):

            # Get first element of key that is a slice
            if type(key_ele) is slice:
                slc_keys = range(*key_ele.indices(self.dict_grid.shape[i]))
                key_list = list(key)

                key_list[i] = None

                has_subslice = any(type(ele) is slice for ele in key_list)

                for slc_key in slc_keys:
                    key_list[i] = slc_key

                    if has_subslice:
                        # If there is a slice left yield generator
                        yield self.cell_array_generator(key_list)

                    else:
                        # No slices? Yield value
                        yield self[tuple(key_list)]

                break

    def _shift_rowcol(self, insertion_point, no_to_insert):
        """Shifts row and column sizes when a table is inserted or deleted"""

        # Shift row heights

        new_row_heights = {}
        del_row_heights = []

        for row, tab in self.row_heights:
            if tab >= insertion_point:
                new_row_heights[(row, tab + no_to_insert)] = \
                    self.row_heights[(row, tab)]
                del_row_heights.append((row, tab))

        for row, tab in new_row_heights:
            self.set_row_height(row, tab, new_row_heights[(row, tab)])

        for row, tab in del_row_heights:
            if (row, tab) not in new_row_heights:
                self.set_row_height(row, tab, None)

        # Shift column widths

        new_col_widths = {}
        del_col_widths = []

        for col, tab in self.col_widths:
            if tab >= insertion_point:
                new_col_widths[(col, tab + no_to_insert)] = \
                    self.col_widths[(col, tab)]
                del_col_widths.append((col, tab))

        for col, tab in new_col_widths:
            self.set_col_width(col, tab, new_col_widths[(col, tab)])

        for col, tab in del_col_widths:
            if (col, tab) not in new_col_widths:
                self.set_col_width(col, tab, None)

    def _adjust_rowcol(self, insertion_point, no_to_insert, axis, tab=None):
        """Adjusts row and column sizes on insertion/deletion"""

        if axis == 2:
            self._shift_rowcol(insertion_point, no_to_insert)
            return

        assert axis in (0, 1)

        cell_sizes = self.col_widths if axis else self.row_heights
        set_cell_size = self.set_col_width if axis else self.set_row_height

        new_sizes = {}
        del_sizes = []

        for pos, table in cell_sizes:
            if pos > insertion_point and (tab is None or tab == table):
                if 0 <= pos + no_to_insert < self.shape[axis]:
                    new_sizes[(pos + no_to_insert, table)] = \
                        cell_sizes[(pos, table)]
                del_sizes.append((pos, table))

        for pos, table in new_sizes:
            set_cell_size(pos, table, new_sizes[(pos, table)])

        for pos, table in del_sizes:
            if (pos, table) not in new_sizes:
                set_cell_size(pos, table, None)

    def _adjust_merge_area(self, attrs, insertion_point, no_to_insert, axis):
        """Returns an updated merge area

        :param attrs: Cell attribute dictionary that shall be adjusted
        :type attrs: dict
        :param insertion_point: Point on axis before insertion takes place
        :type insertion_point: int
        :param no_to_insert: Number of rows/cols/tabs that shall be inserted
        :type no_to_insert: int, >=0
        :param axis: Specifies number of dimension, i.e. 0 == row, 1 == col
        :type axis: int in range(2)

        """

        assert axis in range(2)

        if "merge_area" not in attrs or attrs["merge_area"] is None:
            return

        top, left, bottom, right = attrs["merge_area"]
        selection = Selection([(top, left)], [(bottom, right)], [], [], [])

        selection.insert(insertion_point, no_to_insert, axis)

        __top, __left = selection.block_tl[0]
        __bottom, __right = selection.block_br[0]

        # Adjust merge area if it is beyond the grid shape
        rows, cols, tabs = self.shape

        if __top < 0 and __bottom < 0 or __top >= rows and __bottom >= rows or\
           __left < 0 and __right < 0 or __left >= cols and __right >= cols:
            return

        if __top < 0:
            __top = 0

        if __top >= rows:
            __top = rows - 1

        if __bottom < 0:
            __bottom = 0

        if __bottom >= rows:
            __bottom = rows - 1

        if __left < 0:
            __left = 0

        if __left >= cols:
            __left = cols - 1

        if __right < 0:
            __right = 0

        if __right >= cols:
            __right = cols - 1

        return __top, __left, __bottom, __right

    def _adjust_cell_attributes(self, insertion_point, no_to_insert, axis,
                                tab=None, cell_attrs=None):
        """Adjusts cell attributes on insertion/deletion

        :param insertion_point: Point on axis before insertion
        :type insertion_point: int
        :param no_to_insert: Number of rows/cols/tabs that shall be inserted
        :type no_to_insert: int, >=0
        :param axis: Specifies number of dimension, i.e. 0 == row, 1 == col ...
        :type axis: int in range(3)
        :param tab: Limits insertion to tab for axis < 2
        :type tab: int, optional
        :param cell_attrs: If given replaces the existing CellAttributes
        :type cell_attrs: CellAttributes, optional

        """

        def replace_cell_attributes_table(index, new_table):
            """Replaces table in cell_attributes item"""

            ca = list(list.__getitem__(self.cell_attributes, index))
            ca[1] = new_table
            self.cell_attributes[index] = tuple(ca)

        def get_ca_with_updated_ma(attrs, merge_area):
            """Returns cell attributes with updated merge area"""

            new_attrs = copy(attrs)

            if merge_area is None:
                try:
                    new_attrs.pop("merge_area")
                except KeyError:
                    pass
            else:
                new_attrs["merge_area"] = merge_area

            return new_attrs

        if axis not in list(range(3)):
            raise ValueError("Axis must be in [0, 1, 2]")

        assert tab is None or tab >= 0

        if cell_attrs is None:
            cell_attrs = []

        if cell_attrs:
            self.cell_attributes[:] = cell_attrs

        elif axis < 2:
            # Adjust selections on given table

            ca_updates = {}
            for i, (selection, table, attrs) in enumerate(
                                                    self.cell_attributes):
                selection = copy(selection)
                if tab is None or tab == table:
                    selection.insert(insertion_point, no_to_insert, axis)
                    # Update merge area if present
                    merge_area = self._adjust_merge_area(attrs,
                                                         insertion_point,
                                                         no_to_insert, axis)
                    new_attrs = get_ca_with_updated_ma(attrs, merge_area)

                    ca_updates[i] = selection, table, new_attrs

            for idx in ca_updates:
                self.cell_attributes[idx] = ca_updates[idx]

        elif axis == 2:
            # Adjust tabs

            pop_indices = []

            for i, cell_attribute in enumerate(self.cell_attributes):
                selection, table, value = cell_attribute

                if no_to_insert < 0 and insertion_point <= table:
                    if insertion_point > table + no_to_insert:
                        # Delete later
                        pop_indices.append(i)
                    else:
                        replace_cell_attributes_table(i, table + no_to_insert)

                elif insertion_point < table:
                    # Insert
                    replace_cell_attributes_table(i, table + no_to_insert)

            for i in pop_indices[::-1]:
                self.cell_attributes.pop(i)

        self.cell_attributes._attr_cache.clear()
        self.cell_attributes._update_table_cache()

    def insert(self, insertion_point, no_to_insert, axis, tab=None):
        """Inserts no_to_insert rows/cols/tabs/... before insertion_point

        :param insertion_point: Point on axis before insertion
        :type insertion_point: int
        :param no_to_insert: Number of rows/cols/tabs that shall be inserted
        :type no_to_insert: int, >= 0,
        :param axis: Specifies number of dimension, i.e. 0 == row, 1 == col ...
        :type axis: int
        :param tab: If given then insertion is limited to this tab for axis < 2
        :type tab: int, optional

        """

        if not 0 <= axis <= len(self.shape):
            raise ValueError("Axis not in grid dimensions")

        if insertion_point > self.shape[axis] or \
           insertion_point < -self.shape[axis]:
            raise IndexError("Insertion point not in grid")

        new_keys = {}
        del_keys = []

        for key in list(self.dict_grid.keys()):
            if key[axis] >= insertion_point and (tab is None or tab == key[2]):
                new_key = list(key)
                new_key[axis] += no_to_insert
                if 0 <= new_key[axis] < self.shape[axis]:
                    new_keys[tuple(new_key)] = self(key)
                del_keys.append(key)

        # Now re-insert moved keys

        for key in del_keys:
            if key not in new_keys and self(key) is not None:
                self.pop(key)

        self._adjust_rowcol(insertion_point, no_to_insert, axis, tab=tab)
        self._adjust_cell_attributes(insertion_point, no_to_insert, axis, tab)

        for key in new_keys:
            self.__setitem__(key, new_keys[key])

    def delete(self, deletion_point, no_to_delete, axis, tab=None):
        """Deletes no_to_delete rows/cols/... starting with deletion_point

        Axis specifies number of dimension, i.e. 0 == row, 1 == col, 2 == tab

        """

        if not 0 <= axis < len(self.shape):
            raise ValueError("Axis not in grid dimensions")

        if no_to_delete < 0:
            raise ValueError("Cannot delete negative number of rows/cols/...")

        elif no_to_delete >= self.shape[axis]:
            raise ValueError("Last row/column/table must not be deleted")

        if deletion_point > self.shape[axis] or \
           deletion_point <= -self.shape[axis]:
            raise IndexError("Deletion point not in grid")

        new_keys = {}
        del_keys = []

        # Note that the loop goes over a list that copies all dict keys
        for key in list(self.dict_grid.keys()):
            if tab is None or tab == key[2]:
                if deletion_point <= key[axis] < deletion_point + no_to_delete:
                    del_keys.append(key)

                elif key[axis] >= deletion_point + no_to_delete:
                    new_key = list(key)
                    new_key[axis] -= no_to_delete

                    new_keys[tuple(new_key)] = self(key)
                    del_keys.append(key)

        # Now re-insert moved keys

        for key in new_keys:
            self.__setitem__(key, new_keys[key])

        for key in del_keys:
            if key not in new_keys and self(key) is not None:
                self.pop(key)

        self._adjust_rowcol(deletion_point, -no_to_delete, axis, tab=tab)
        self._adjust_cell_attributes(deletion_point, -no_to_delete, axis, tab)

    def set_row_height(self, row, tab, height):
        """Sets row height"""

        try:
            self.row_heights.pop((row, tab))
        except KeyError:
            pass

        if height is not None:
            self.row_heights[(row, tab)] = float(height)

    def set_col_width(self, col, tab, width):
        """Sets column width"""

        try:
            self.col_widths.pop((col, tab))
        except KeyError:
            pass

        if width is not None:
            self.col_widths[(col, tab)] = float(width)

    # Element access via call

    __call__ = __getitem__

# End of class DataArray

# -----------------------------------------------------------------------------


class CodeArray(DataArray):
    """CodeArray provides objects when accessing cells via `__getitem__`

    Cell code can be accessed via function call

    This class represents layer 3 of the model.

    """

    # Cache for results from __getitem__ calls
    result_cache = {}

    # Cache for frozen objects
    frozen_cache = {}

    # Custom font storage
    custom_fonts = {}

    def __setitem__(self, key, value):
        """Sets cell code and resets result cache"""

        # Change numpy array repr function for grid cell results
        numpy.set_string_function(lambda s: repr(s.tolist()))

        # Prevent unchanged cells from being recalculated on cursor movement

        repr_key = repr(key)

        unchanged = (repr_key in self.result_cache and
                     value == self(key)) or \
                    ((value is None or value == "") and
                     repr_key not in self.result_cache)

        super().__setitem__(key, value)

        if not unchanged:
            # Reset result cache
            self.result_cache = {}

    def __getitem__(self, key):
        """Returns _eval_cell"""

        if all(type(k) is not slice for k in key):
            # Button cell handling
            if self.cell_attributes[key]["button_cell"] is not False:
                return
            # Frozen cell handling
            frozen_res = self.cell_attributes[key]["frozen"]
            if frozen_res:
                if repr(key) in self.frozen_cache:
                    return self.frozen_cache[repr(key)]
                else:
                    # Frozen cache is empty.
                    # Maybe we have a reload without the frozen cache
                    result = self._eval_cell(key, self(key))
                    self.frozen_cache[repr(key)] = result
                    return result

        # Normal cell handling

        if repr(key) in self.result_cache:
            return self.result_cache[repr(key)]

        elif self(key) is not None:
            result = self._eval_cell(key, self(key))
            self.result_cache[repr(key)] = result

            return result

    def _make_nested_list(self, gen):
        """Makes nested list from generator for creating numpy.array"""

        res = []

        for ele in gen:
            if ele is None:
                res.append(None)

            elif not isstring(ele) and isgenerator(ele):
                # Nested generator
                res.append(self._make_nested_list(ele))

            else:
                res.append(ele)

        return res

    def _get_updated_environment(self, env_dict=None):
        """Returns globals environment with 'magic' variable

        :param env_dict: Maps global variable name to value
        :type env_dict: dict, optional, defaults to {'S': self}

        """

        if env_dict is None:
            env_dict = {'S': self}

        env = globals().copy()
        env.update(env_dict)

        return env

    def exec_then_eval(self, code, _globals=None, _locals=None):
        """execs multuiline code and returns eval of last code line"""

        if _globals is None:
            _globals = {}

        if _locals is None:
            _locals = {}

        block = ast.parse(code, mode='exec')

        # assumes last node is an expression
        last_body = block.body.pop()
        last = ast.Expression(last_body.value)

        exec(compile(block, '<string>', mode='exec'), _globals, _locals)
        res = eval(compile(last, '<string>', mode='eval'), _globals, _locals)

        if hasattr(last_body, "targets"):
            for target in last_body.targets:
                _globals[target.id] = res

        globals().update(_globals)

        return res

    def _eval_cell(self, key, code):
        """Evaluates one cell and returns its result"""

        # Flatten helper function
        def nn(val):
            """Returns flat numpy array without None values"""
            try:
                return numpy.array([_f for _f in val.flat if _f])

            except AttributeError:
                # Probably no numpy array
                return numpy.array([_f for _f in val if _f])

        # Set up environment for evaluation
        from matplotlib.figure import Figure  # Needs to be imported here
        env_dict = {'X': key[0], 'Y': key[1], 'Z': key[2], 'bz2': bz2,
                    'base64': base64, 'nn': nn, 'Figure': Figure,
                    'R': key[0], 'C': key[1], 'T': key[2], 'S': self}
        env = self._get_updated_environment(env_dict=env_dict)

        # Return cell value if in safe mode

        if self.safe_mode:
            return code

        # If cell is not present return None

        if code is None:
            return

        elif isgenerator(code):
            # We have a generator object

            return numpy.array(self._make_nested_list(code), dtype="O")

        try:
            import signal

            signal.signal(signal.SIGALRM, self.handler)
            signal.alarm(self.settings.timeout)

        except Exception:
            # No POSIX system
            pass

        try:
            result = self.exec_then_eval(code, env, {})

        except AttributeError as err:
            # Attribute Error includes RunTimeError
            result = AttributeError(err)

        except RuntimeError as err:
            result = RuntimeError(err)

        except Exception as err:
            result = Exception(err)

        finally:
            try:
                signal.alarm(0)
            except Exception:
                # No POSIX system
                pass

        # Change back cell value for evaluation from other cells
        # self.dict_grid[key] = _old_code

        return result

    def pop(self, key):
        """pop with cache support

        :param key: Cell key that shall be popped
        :type key: tuple

        """

        try:
            self.result_cache.pop(repr(key))

        except KeyError:
            pass

        return super().pop(key)

    def reload_modules(self):
        """Reloads modules that are available in cells"""

        from importlib import reload
        modules = [bz2, base64, re, ast, sys, numpy, datetime]

        for module in modules:
            reload(module)

    def clear_globals(self):
        """Clears all newly assigned globals"""

        base_keys = ['cStringIO', 'KeyValueStore', 'UnRedo',
                     'isgenerator', 'isstring', 'bz2', 'base64',
                     '__package__', 're', '__doc__', 'QPixmap', 'charts',
                     'CellAttributes', 'product', 'ast', '__builtins__',
                     '__file__', 'sys', 'isslice', '__name__', 'QImage',
                     'copy', 'imap', 'ifilter', 'Selection', 'DictGrid',
                     'numpy', 'CodeArray', 'DataArray', 'datetime']

        for key in list(globals().keys()):
            if key not in base_keys:
                globals().pop(key)

    def get_globals(self):
        """Returns globals dict"""

        return globals()

    def execute_macros(self):
        """Executes all macros and returns result string

        Executes macros only when not in safe_mode

        """

        if self.safe_mode:
            return '', "Safe mode activated. Code not executed."

        # We need to execute each cell so that assigned globals are updated
        for key in self:
            self[key]

        # Windows exec does not like Windows newline
        self.macros = self.macros.replace('\r\n', '\n')

        # Set up environment for evaluation
        globals().update(self._get_updated_environment())

        # Create file-like string to capture output
        import io
        code_out = io.StringIO()
        code_err = io.StringIO()
        err_msg = io.StringIO()

        # Capture output and errors
        sys.stdout = code_out
        sys.stderr = code_err

        try:
            import signal

            signal.signal(signal.SIGALRM, self.handler)
            signal.alarm(self.settings.timeout)

        except Exception:
            # No POSIX system
            pass

        try:
            exec(self.macros, globals())
            try:
                signal.alarm(0)
            except Exception:
                # No POSIX system
                pass

        except Exception:
            # Print exception
            # (Because of how the globals are handled during execution
            # we must import modules here)
            from traceback import print_exception
            from lib.exception_handling import get_user_codeframe
            exc_info = sys.exc_info()
            user_tb = get_user_codeframe(exc_info[2]) or exc_info[2]
            print_exception(exc_info[0], exc_info[1], user_tb, None, err_msg)
        # Restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        results = code_out.getvalue()
        errs = code_err.getvalue() + err_msg.getvalue()

        code_out.close()
        code_err.close()

        # Reset result cache
        self.result_cache.clear()

        # Reset frozen cache
        self.frozen_cache.clear()
        return results, errs

    def _sorted_keys(self, keys, startkey, reverse=False):
        """Generator that yields sorted keys starting with startkey

        :param keys: Key sequence that is sorted
        :type keys: Iterable of tuple
        :param startkey: First key to be yielded
        :type startkey: tuple
        :param reverse: Sort direction reversed if True
        :type reverse: bool, optional, defaults to False

        """

        def tuple_key(t):
            return t[::-1]

        if reverse:
            def tuple_cmp(t):
                return t[::-1] > startkey[::-1]
        else:
            def tuple_cmp(t):
                return t[::-1] < startkey[::-1]

        searchkeys = sorted(keys, key=tuple_key, reverse=reverse)
        searchpos = sum(1 for _ in filter(tuple_cmp, searchkeys))

        searchkeys = searchkeys[searchpos:] + searchkeys[:searchpos]

        for key in searchkeys:
            yield key

    def string_match(self, datastring, findstring, word, case, regexp):
        """Returns position of findstring in datastring or None if not found

        :param word: Search full words only if True
        :type word: bool
        :param case: Search case sensitively if True
        :type case: bool
        :param regexp: Regular expression search if True
        :rtype: int or None
        :return: Position of findstring in datastring or None if not found

        """

        if not isinstance(datastring, str):  # Empty cell
            return

        if regexp:
            match = re.search(findstring, datastring)
            if match is None:
                pos = -1
            else:
                pos = match.start()
        else:
            if not case:
                datastring = datastring.lower()
                findstring = findstring.lower()

            if word:
                pos = -1
                matchstring = r'\b' + findstring + r'+\b'
                for match in re.finditer(matchstring, datastring):
                    pos = match.start()
                    break  # find 1st occurrance
            else:
                pos = datastring.find(findstring)

        if pos == -1:
            return None
        else:
            return pos

    def findnextmatch(self, startkey, find_string, up=False, word=False,
                      case=False, regexp=False, results=True):
        """the position of the next match of find_string

        :param startkey: Start position of search
        :type startkey: tuple
        :param find_string: String to be searched for
        :type startkey: str
        :param up: Search up instead of down if True
        :type up: bool, optional, defaults to False
        :param word: Search full words only if True
        :type word: bool, optional, defaults to False
        :param case: Search case sensitively if True
        :type case: bool, optional, defaults to False
        :param regexp: Reg. expression search if True
        :type regexp: bool, optional, defaults to False
        :param results: Search includes result string if True (slower)
        :type results: bool, optional, defaults to True
        :rtype: str or None
        :return:  Returns tuple with position of the next match of find_string

        """

        if results:
            def is_matching(key, find_string, word, case, regexp):
                code = self(key)
                pos = self.string_match(code, find_string, word, case, regexp)
                if pos is not None:
                    return True
                else:
                    res_str = str(self[key])
                    pos = self.string_match(res_str, find_string, word, case,
                                            regexp)
                    return pos is not None

        else:
            def is_matching(code, find_string, word, case, regexp):
                code = self(key)
                pos = self.string_match(code, find_string, word, case, regexp)
                return pos is not None

        # List of keys in sgrid in search order

        table = startkey[2]
        keys = [key for key in self.keys() if key[2] == table]

        for key in self._sorted_keys(keys, startkey, reverse=up):
            try:
                if is_matching(key, find_string, word, case, regexp):
                    return key

            except Exception:
                # re errors are cryptical: sre_constants,...
                pass

    def handler(self, signum, frame):
        raise RuntimeError("Timeout after {} s.".format(self.settings.timeout))

# End of class CodeArray
