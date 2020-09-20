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


**Provides**

 * :class:`DefaultCellAttributeDict`
 * :class:`CellAttribute`
 * :class:`CellAttributes`
 * :class:`KeyValueStore`
 * :class:`DictGrid`
 * :class:`DataArray`
 * :class:`CodeArray`

"""

from __future__ import absolute_import
from builtins import filter
from builtins import str
from builtins import zip
from builtins import range

import ast
import base64
import bz2
from collections import defaultdict
from copy import copy
import datetime
from importlib import reload
from inspect import isgenerator
import io
from itertools import product
import re
import signal
import sys
from traceback import print_exception
from typing import (
        Any, Dict, Iterable, List, NamedTuple, Sequence, Tuple, Union)

import numpy
from PyQt5.QtGui import QImage, QPixmap
try:
    from matplotlib.figure import Figure
except ImportError:
    Figure = None

try:
    from pyspread.settings import Settings
    from pyspread.lib.attrdict import AttrDict
    import pyspread.lib.charts as charts
    from pyspread.lib.exception_handling import get_user_codeframe
    from pyspread.lib.typechecks import is_stringlike
    from pyspread.lib.selection import Selection
except ImportError:
    from settings import Settings
    from lib.attrdict import AttrDict
    import lib.charts as charts
    from lib.exception_handling import get_user_codeframe
    from lib.typechecks import is_stringlike
    from lib.selection import Selection


class DefaultCellAttributeDict(AttrDict):
    """Holds default values for all cell attributes"""

    def __init__(self):
        super().__init__(self)

        self.borderwidth_bottom = 1
        self.borderwidth_right = 1
        self.bordercolor_bottom = None
        self.bordercolor_right = None
        self.bgcolor = 255, 255, 255  # Do not use theme
        self.textfont = None
        self.pointsize = 10
        self.fontweight = None
        self.fontstyle = None
        self.textcolor = 0, 0, 0  # Do not use theme
        self.underline = False
        self.strikethrough = False
        self.locked = False
        self.angle = 0.0
        self.vertical_align = "align_top"
        self.justification = "justify_left"
        self.frozen = False
        self.merge_area = None
        self.renderer = "text"
        self.button_cell = False
        self.panel_cell = False


class CellAttribute(NamedTuple):
    """Single cell attribute"""

    selection: Selection
    table: int
    attr: AttrDict


class CellAttributes(list):
    """Stores cell formatting attributes in a list of CellAttribute instances

    The class stores cell attributes as a list of layers.
    Each layer describes attributes for one selection in one table.
    Ultimately, a cell's attributes are determined by going through all
    elements of an `CellAttributes` instance. A default `AttrDict` is updated
    with the one in the list element if it is relevant for the respective cell.
    Therefore, attributes are efficiently stored for large sets of cells.

    The class provides attribute read access to single cells via
    :meth:`__getitem__`.
    Otherwise it behaves similar to a `list`.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    # Cache for __getattr__ maps key to tuple of len and attr_dict

    _attr_cache = AttrDict()
    _table_cache = {}

    def append(self, cell_attribute: CellAttribute):
        """append that clears caches

        :param cell_attribute: Cell attribute to be appended

        """

        if not isinstance(cell_attribute, CellAttribute):
            msg = "{} not instance of CellAttribute".format(cell_attribute)
            raise Warning(msg)
            return

        # We need to clean up merge areas
        selection, table, attr = cell_attribute
        if "merge_area" in attr:
            for i, ele in enumerate(reversed(self)):
                if ele[0] == selection and ele[1] == table \
                   and "merge_area" in ele[2]:
                    try:
                        self.pop(-1 - i)
                    except IndexError:
                        pass
            if attr["merge_area"] is not None:
                super().append(cell_attribute)
        else:
            super().append(cell_attribute)

        self._attr_cache.clear()
        self._table_cache.clear()

    def __getitem__(self, key: Tuple[int, int, int]) -> AttrDict:
        """Returns attribute dict for a single key

        :param key: Key of cell for cell_attribute retrieval

        """

#        if any(isinstance(key_ele, slice) for key_ele in key):
#            raise Warning("slice in key {}".format(key))
#            return

        try:
            cache_len, cache_dict = self._attr_cache[key]

            # Use cache result only if no new attrs have been defined
            if cache_len == len(self):
                return cache_dict
        except KeyError:
            pass

        # Update table cache if it is outdated (e.g. when creating a new grid)
        if len(self) != self._len_table_cache():
            self._update_table_cache()

        row, col, tab = key

        result_dict = DefaultCellAttributeDict()

        try:
            for selection, attr_dict in self._table_cache[tab]:
                if (row, col) in selection:
                    result_dict.update(attr_dict)
        except KeyError:
            pass

        # Upddate cache with current length and dict
        self._attr_cache[key] = (len(self), result_dict)

        return result_dict

    def __setitem__(self, index: int, cell_attribute: CellAttribute):
        """__setitem__ that clears caches

        :param index: Index of item in self
        :param cell_attribute: Cell attribute to be set

        """

        if not isinstance(cell_attribute, CellAttribute):
            msg = "{} not instance of CellAttribute".format(cell_attribute)
            raise Warning(msg)
            return

        super().__setitem__(index, cell_attribute)

        self._attr_cache.clear()
        self._table_cache.clear()

    def _len_table_cache(self) -> int:
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

        if len(self) != self._len_table_cache():
            raise Warning("Length of _table_cache does not match")

    def get_merging_cell(self,
                         key: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Returns key of cell that merges the cell key

        Retuns None if cell key not merged.

        :param key: Key of the cell that is merged

        """

        row, col, tab = key

        # Is cell merged
        for selection, table, attr in self:
            if tab == table and "merge_area" in attr:
                top, left, bottom, right = attr["merge_area"]
                if top <= row <= bottom and left <= col <= right:
                    return top, left, tab

    def for_table(self, table: int) -> list:
        """Return cell attributes for a given table

        Return type should be `CellAttributes`. The list return type is
        provided because PEP 563 is unavailable in Python 3.6.

        Note that the table's presence in the grid is not checked.

        :param table: Table for which cell attributes are returned

        """

        table_cell_attributes = CellAttributes()

        for selection, __table, attr in self:
            if __table == table:
                cell_attribute = CellAttribute(selection, __table, attr)
                table_cell_attributes.append(cell_attribute)

        return table_cell_attributes

# End of class CellAttributes


class KeyValueStore(dict):
    """Key-Value store in memory. Currently a dict with default value None.

    This class represents layer 0 of the model.

    """

    def __init__(self, default_value=None):
        """
        :param default_value: Value that is provided for missing keys

        """

        super().__init__()
        self.default_value = default_value

    def __missing__(self, value: Any) -> Any:
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

    """

    def __init__(self, shape: Tuple[int, int, int]):
        """
        :param shape: Shape of the grid

        """

        super().__init__()

        self.shape = shape

        # Instance of :class:`CellAttributes`
        self.cell_attributes = CellAttributes()

        # Macros as string
        self.macros = u""

        self.row_heights = defaultdict(float)  # Keys have format (row, table)
        self.col_widths = defaultdict(float)  # Keys have format (col, table)

    def __getitem__(self, key: Tuple[int, int, int]) -> Any:
        """
        :param key: Cell key

        """
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

    """

    def __init__(self, shape: Tuple[int, int, int], settings: Settings):
        """
        :param shape: Shape of the grid
        :param settings: Pyspread settings

        """

        self.dict_grid = DictGrid(shape)
        self.settings = settings

    def __eq__(self, other) -> bool:
        if not hasattr(other, "dict_grid") or \
           not hasattr(other, "cell_attributes"):
            return False

        return self.dict_grid == other.dict_grid and \
            self.cell_attributes == other.cell_attributes

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    @property
    def data(self) -> dict:
        """Returns `dict` of data content.


        - Data is the central content interface for loading / saving data.
        - It shall be used for loading and saving from and to `.pys` and other
          files.
        - It shall be used for loading and saving macros.
        - However, it is not used for importing and exporting data because
          these operations are partial to the grid.

        **Content of returned dict**

        :param shape: Grid shape
        :type shape: Tuple[int, int, int]
        :param grid: Cell content
        :type grid: Dict[Tuple[int, int, int], str]
        :param attributes: Cell attributes
        :type attributes: CellAttribute
        :param row_heights: Row heights
        :type row_heights: defaultdict[Tuple[int, int], float]
        :param col_widths: Column widths
        :type col_widths: defaultdict[Tuple[int, int], float]
        :param macros: Macros
        :type macros: str

        """

        data = {}

        data["shape"] = self.shape
        data["grid"] = {}.update(self.dict_grid)
        data["attributes"] = self.cell_attributes[:]
        data["row_heights"] = self.row_heights
        data["col_widths"] = self.col_widths
        data["macros"] = self.macros

        return data

    @data.setter
    def data(self, **kwargs):
        """Sets data from given parameters

        Old values are deleted.
        If a paremeter is not given, nothing is changed.

        **Content of kwargs dict**

        :param shape: Grid shape
        :type shape: Tuple[int, int, int]
        :param grid: Cell content
        :type grid: Dict[Tuple[int, int, int], str]
        :param attributes: Cell attributes
        :type attributes: CellAttribute
        :param row_heights: Row heights
        :type row_heights: defaultdict[Tuple[int, int], float]
        :param col_widths: Column widths
        :type col_widths: defaultdict[Tuple[int, int], float]
        :param macros: Macros
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
    def row_heights(self) -> defaultdict:
        """row_heights interface to dict_grid"""

        return self.dict_grid.row_heights

    @row_heights.setter
    def row_heights(self, row_heights: defaultdict):
        """row_heights interface to dict_grid"""

        self.dict_grid.row_heights = row_heights

    @property
    def col_widths(self) -> defaultdict:
        """col_widths interface to dict_grid"""

        return self.dict_grid.col_widths

    @col_widths.setter
    def col_widths(self, col_widths: defaultdict):
        """col_widths interface to dict_grid"""

        self.dict_grid.col_widths = col_widths

    @property
    def cell_attributes(self) -> CellAttributes:
        """cell_attributes interface to dict_grid"""

        return self.dict_grid.cell_attributes

    @cell_attributes.setter
    def cell_attributes(self, value: CellAttributes):
        """cell_attributes interface to dict_grid"""

        # First empty cell_attributes
        self.cell_attributes[:] = []
        self.cell_attributes.extend(value)

    @property
    def macros(self) -> str:
        """macros interface to dict_grid"""

        return self.dict_grid.macros

    @macros.setter
    def macros(self, macros: str):
        """Sets  macros string"""

        self.dict_grid.macros = macros

    @property
    def shape(self) -> Tuple[int, int, int]:
        """Returns dict_grid shape"""

        return self.dict_grid.shape

    @shape.setter
    def shape(self, shape: Tuple[int, int, int]):
        """Deletes all cells beyond new shape and sets dict_grid shape

        Returns a dict of the deleted cells' contents

        :param shape: Target shape for grid

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

    def __iter__(self) -> Iterable:
        """Returns iterator over self.dict_grid"""

        return iter(self.dict_grid)

    def __contains__(self, key: Tuple[int, int, int]) -> bool:
        """True if key is contained in grid

        Handles single keys only.

        :param key: Key of cell to be checked

        """

        if any(not isinstance(ele, int) for ele in key):
            return NotImplemented

        row, column, table = key
        rows, columns, tables = self.shape

        return (0 <= row <= rows
                and 0 <= column <= columns
                and 0 <= table <= tables)

    # Slice support

    def __getitem__(self, key: Tuple[Union[int, slice], Union[int, slice],
                                     Union[int, slice]]
                    ) -> Union[str, Iterable[str], Iterable[Iterable[str]],
                               Iterable[Iterable[Iterable[str]]]]:
        """Adds slicing access to cell code retrieval

        The cells are returned as a generator of generators, of ... of unicode.

        :param key: Keys of the cell code that is returned

        Note
        ----
        Classical Excel type addressing (A$1, ...) may be added here later

        """

        for key_ele in key:
            if isinstance(key_ele, slice):
                # We have something slice-like here
                return self.cell_array_generator(key)

            if is_stringlike(key_ele):
                # We have something string-like here
                msg = "Cell string based access not implemented"
                raise NotImplementedError(msg)

        # key_ele should be a single cell

        return self.dict_grid[key]

    def __setitem__(self, key: Tuple[Union[int, slice], Union[int, slice],
                                     Union[int, slice]], value: str):
        """Accepts index and slice keys

        :param key: Cell key(s) that shall be set
        :param value: Code for cell(s) to be set

        """

        single_keys_per_dim = []

        for axis, key_ele in enumerate(key):
            if isinstance(key_ele, slice):
                # We have something slice-like here

                length = key[axis]
                slice_range = range(*key_ele.indices(length))
                single_keys_per_dim.append(slice_range)

            elif is_stringlike(key_ele):
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

    def __getstate__(self) -> Dict[str, DictGrid]:
        """Returns dict_grid for pickling

        Note that all persistent data is contained in the DictGrid class

        """

        return {"dict_grid": self.dict_grid}

    def get_row_height(self, row: int, tab: int) -> float:
        """Returns row height

        :param row: Row for which height is retrieved
        :param tab: Table for which for which row height is retrieved

        """

        try:
            return self.row_heights[(row, tab)]

        except KeyError:
            return

    def get_col_width(self, col: int, tab: int) -> float:
        """Returns column width

        :param col: Column for which width is retrieved
        :param tab: Table for which for which column width is retrieved

        """

        try:
            return self.col_widths[(col, tab)]

        except KeyError:
            return

    def keys(self) -> List[Tuple[int, int, int]]:
        """Returns keys in self.dict_grid"""

        return list(self.dict_grid.keys())

    def pop(self, key: Tuple[int, int, int]) -> Any:
        """dict_grid pop wrapper

        :param key: Cell key

        """

        return self.dict_grid.pop(key)

    def get_last_filled_cell(self, table: int = None) -> Tuple[int, int, int]:
        """Returns key for the bottommost rightmost cell with content

        :param table: Limit search to this table

        """

        maxrow = 0
        maxcol = 0

        for row, col, tab in self.dict_grid:
            if table is None or tab == table:
                maxrow = max(row, maxrow)
                maxcol = max(col, maxcol)

        return maxrow, maxcol, table

    def cell_array_generator(self,
                             key: Tuple[Union[int, slice], Union[int, slice],
                                        Union[int, slice]]) -> Iterable[str]:
        """Generator traversing cells specified in key

        Yields cells' contents.

        :param key: Specifies the cell keys of the generator

        """

        for i, key_ele in enumerate(key):

            # Get first element of key that is a slice
            if isinstance(key_ele, slice):
                slc_keys = range(*key_ele.indices(self.dict_grid.shape[i]))
                key_list = list(key)

                key_list[i] = None

                has_subslice = any(isinstance(ele, slice) for ele in key_list)

                for slc_key in slc_keys:
                    key_list[i] = slc_key

                    if has_subslice:
                        # If there is a slice left yield generator
                        yield self.cell_array_generator(key_list)

                    else:
                        # No slices? Yield value
                        yield self[tuple(key_list)]

                break

    def _shift_rowcol(self, insertion_point: int, no_to_insert: int):
        """Shifts row and column sizes when a table is inserted or deleted

        :param insertion_point: Table at which a new table is inserted
        :param no_to_insert: Number of tables that are inserted

        """

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

    def _adjust_rowcol(self, insertion_point: int, no_to_insert: int,
                       axis: int, tab: int = None):
        """Adjusts row and column sizes on insertion/deletion

        :param insertion_point: Point on axis at which insertion takes place
        :param no_to_insert: Number of rows or columns that are inserted
        :param axis: Row insertion if 0, column insertion if 1, must be in 0, 1
        :param tab: Table at which insertion takes place, None means all tables

        """

        if axis == 2:
            self._shift_rowcol(insertion_point, no_to_insert)
            return

        if axis not in (0, 1):
            raise Warning("Axis {} not in (0, 1)".format(axis))
            return

        cell_sizes = self.col_widths if axis else self.row_heights
        set_cell_size = self.set_col_width if axis else self.set_row_height

        new_sizes = {}
        del_sizes = []

        for pos, table in cell_sizes:
            if pos >= insertion_point and (tab is None or tab == table):
                if 0 <= pos + no_to_insert < self.shape[axis]:
                    new_sizes[(pos + no_to_insert, table)] = \
                        cell_sizes[(pos, table)]
                if pos < insertion_point + no_to_insert:
                    new_sizes[(pos, table)] = cell_sizes[(pos, table)]
                del_sizes.append((pos, table))

        for pos, table in new_sizes:
            set_cell_size(pos, table, new_sizes[(pos, table)])

        for pos, table in del_sizes:
            if (pos, table) not in new_sizes:
                set_cell_size(pos, table, None)

    def _adjust_merge_area(
            self, attrs: AttrDict, insertion_point: int, no_to_insert: int,
            axis: int) -> Tuple[int, int, int, int]:
        """Returns an updated merge area

        :param attrs: Cell attribute dictionary that shall be adjusted
        :param insertion_point: Point on axis at which insertion takes place
        :param no_to_insert: Number of rows/cols/tabs to be inserted (>=0)
        :param axis: Row insertion if 0, column insertion if 1, must be in 0, 1

        """

        if axis not in (0, 1):
            raise Warning("Axis {} not in (0, 1)".format(axis))
            return

        if "merge_area" not in attrs or attrs["merge_area"] is None:
            return

        top, left, bottom, right = attrs["merge_area"]
        selection = Selection([(top, left)], [(bottom, right)], [], [], [])

        selection.insert(insertion_point, no_to_insert, axis)

        __top, __left = selection.block_tl[0]
        __bottom, __right = selection.block_br[0]

        # Adjust merge area if it is beyond the grid shape
        rows, cols, tabs = self.shape

        if __top < 0 and __bottom < 0:
            return
        if __top >= rows and __bottom >= rows:
            return
        if __left < 0 and __right < 0:
            return
        if __left >= cols and __right >= cols:
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

    def _adjust_cell_attributes(
            self, insertion_point: int, no_to_insert: int,  axis: int,
            tab: int = None, cell_attrs: AttrDict = None):
        """Adjusts cell attributes on insertion/deletion

        :param insertion_point: Point on axis at which insertion takes place
        :param no_to_insert: Number of rows/cols/tabs to be inserted (>=0)
        :param axis: Row insertion if 0, column insertion if 1, must be in 0, 1
        :param tab: Table at which insertion takes place, None means all tables
        :param cell_attrs: If given replaces the existing cell attributes

        """

        def replace_cell_attributes_table(index: int, new_table: int):
            """Replaces table in cell_attributes item

            :param index: Cell attribute index for table replacement
            :param new_table: New table value for cell attribute

            """

            cell_attr = list(list.__getitem__(self.cell_attributes, index))
            cell_attr[1] = new_table
            self.cell_attributes[index] = CellAttribute(*cell_attr)

        def get_ca_with_updated_ma(
                attrs: AttrDict,
                merge_area: Tuple[int, int, int, int]) -> AttrDict:
            """Returns cell attributes with updated merge area

            :param attrs: Cell attributes to be updated
            :param merge_area: New merge area (top, left, bottom, right)

            """

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

        if tab is not None and tab < 0:
            raise Warning("tab is negative")
            return

        if cell_attrs is None:
            cell_attrs = []

        if cell_attrs:
            self.cell_attributes[:] = cell_attrs

        elif axis < 2:
            # Adjust selections on given table

            ca_updates = {}
            for i, (selection, table, attrs) \
                    in enumerate(self.cell_attributes):
                selection = copy(selection)
                if tab is None or tab == table:
                    selection.insert(insertion_point, no_to_insert, axis)
                    # Update merge area if present
                    merge_area = self._adjust_merge_area(attrs,
                                                         insertion_point,
                                                         no_to_insert, axis)
                    new_attrs = get_ca_with_updated_ma(attrs, merge_area)

                    ca_updates[i] = CellAttribute(selection, table, new_attrs)

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

                elif insertion_point <= table:
                    # Insert
                    replace_cell_attributes_table(i, table + no_to_insert)

            for i in pop_indices[::-1]:
                self.cell_attributes.pop(i)

        self.cell_attributes._attr_cache.clear()
        self.cell_attributes._update_table_cache()

    def insert(self, insertion_point: int, no_to_insert: int, axis: int,
               tab: int = None):
        """Inserts no_to_insert rows/cols/tabs/... before insertion_point

        :param insertion_point: Point on axis at which insertion takes place
        :param no_to_insert: Number of rows/cols/tabs to be inserted (>=0)
        :param axis: Row/Column/Table insertion if 0/1/2 must be in 0, 1, 2
        :param tab: Table at which insertion takes place, None means all tables

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

    def delete(self, deletion_point: int, no_to_delete: int, axis: int,
               tab: int = None):
        """Deletes no_to_delete rows/cols/... starting with deletion_point

        :param deletion_point: Point on axis at which deletion takes place
        :param no_to_delete: Number of rows/cols/tabs to be deleted (>=0)
        :param axis: Row/Column/Table deletion if 0/1/2, must be in 0, 1, 2
        :param tab: Table at which insertion takes place, None means all tables

        """

        if not 0 <= axis < len(self.shape):
            raise ValueError("Axis not in grid dimensions")

        if no_to_delete < 0:
            raise ValueError("Cannot delete negative number of rows/cols/...")

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

    def set_row_height(self, row: int, tab: int, height: float):
        """Sets row height

        :param row: Row for height setting
        :param tab: Table, in which row height is set
        :param height: Row height to be set

        """

        try:
            self.row_heights.pop((row, tab))
        except KeyError:
            pass

        if height is not None:
            self.row_heights[(row, tab)] = float(height)

    def set_col_width(self, col: int, tab: int, width: float):
        """Sets column width

        :param col: Column for width setting
        :param tab: Table, in which column width is set
        :param width: Column width to be set

        """

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

    # Safe mode: If True then Whether pyspread is operating in safe_mode
    # In safe_mode, cells are not evaluated but its code is returned instead.
    safe_mode = False

    def __setitem__(self, key: Tuple[Union[int, slice], Union[int, slice],
                                     Union[int, slice]], value: str):
        """Sets cell code and resets result cache

        :param key: Cell key(s) that shall be set
        :param value: Code for cell(s) to be set

        """

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

    def __getitem__(self, key: Tuple[Union[int, slice], Union[int, slice],
                                     Union[int, slice]]) -> Any:
        """Returns _eval_cell

        :param key: Cell key for result retrieval (code if in safe mode)

        """

        if not any(isinstance(k, slice) for k in key):
            # Button cell handling
            if self.cell_attributes[key].button_cell is not False:
                return
            # Frozen cell handling
            frozen_res = self.cell_attributes[key].frozen
            if frozen_res:
                if repr(key) in self.frozen_cache:
                    return self.frozen_cache[repr(key)]
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

    def _make_nested_list(self, gen: Union[Iterable, Iterable[Iterable],
                                           Iterable[Iterable[Iterable]]]
                          ) -> Union[Sequence, Sequence[Sequence],
                                     Sequence[Sequence[Sequence]]]:
        """Makes nested list from generator for creating numpy.array"""

        res = []

        for ele in gen:
            if ele is None:
                res.append(None)

            elif not is_stringlike(ele) and isgenerator(ele):
                # Nested generator
                res.append(self._make_nested_list(ele))

            else:
                res.append(ele)

        return res

    def _get_updated_environment(self, env_dict: dict = None) -> dict:
        """Returns globals environment with 'magic' variable

        :param env_dict: Maps global variable name to value, None: {'S': self}

        """

        if env_dict is None:
            env_dict = {'S': self}

        env = globals().copy()
        env.update(env_dict)

        return env

    def exec_then_eval(self, code: str,
                       _globals: dict = None, _locals: dict = None):
        """execs multuiline code and returns eval of last code line

        :param code: Code to be executed / evaled
        :param _globals: Globals dict for code execution and eval
        :param _locals: Locals dict for code execution and eval

        """

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

    def _eval_cell(self, key: Tuple[int, int, int], code: str) -> Any:
        """Evaluates one cell and returns its result

        :param key: Key of cell to be evaled
        :param code: Code to be evaled

        """

        # Flatten helper function
        def nn(val: numpy.array) -> numpy.array:
            """Returns flat numpy array without None values"""
            try:
                return numpy.array([_f for _f in val.flat if _f is not None],
                                   dtype="O")

            except AttributeError:
                # Probably no numpy array
                return numpy.array([_f for _f in val if _f is not None],
                                   dtype="O")

        env_dict = {'X': key[0], 'Y': key[1], 'Z': key[2], 'bz2': bz2,
                    'base64': base64, 'nn': nn, 'Figure': Figure,
                    'R': key[0], 'C': key[1], 'T': key[2], 'S': self}
        env = self._get_updated_environment(env_dict=env_dict)

        if self.safe_mode:
            # Safe mode is active
            return code

        if code is None:
            # Cell is not present
            return

        if isgenerator(code):
            # We have a generator object
            return numpy.array(self._make_nested_list(code), dtype="O")

        try:
            signal.signal(signal.SIGALRM, self.handler)
            signal.alarm(self.settings.timeout)
        except AttributeError:
            # No Unix system
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
            except AttributeError:
                # No POSIX system
                pass

        # Change back cell value for evaluation from other cells
        # self.dict_grid[key] = _old_code

        return result

    def pop(self, key: Tuple[int, int, int]):
        """pop with cache support

        :param key: Cell key that shall be popped

        """

        try:
            self.result_cache.pop(repr(key))

        except KeyError:
            pass

        return super().pop(key)

    def reload_modules(self):
        """Reloads modules that are available in cells"""

        modules = [bz2, base64, re, ast, sys, numpy, datetime]

        for module in modules:
            reload(module)

    def clear_globals(self):
        """Clears all newly assigned globals"""

        base_keys = ['cStringIO', 'KeyValueStore', 'UnRedo', 'Figure',
                     'reload', 'io', 'print_exception', 'get_user_codeframe',
                     'isgenerator', 'is_stringlike', 'bz2', 'base64',
                     '__package__', 're', '__doc__', 'QPixmap', 'charts',
                     'product', 'AttrDict', 'CellAttribute', 'CellAttributes',
                     'DefaultCellAttributeDict', 'ast', '__builtins__',
                     '__file__', 'sys', '__name__', 'QImage', 'defaultdict',
                     'copy', 'imap', 'ifilter', 'Selection', 'DictGrid',
                     'numpy', 'CodeArray', 'DataArray', 'datetime', 'signal',
                     'Any', 'Dict', 'Iterable', 'List', 'NamedTuple',
                     'Sequence', 'Tuple', 'Union']

        for key in list(globals().keys()):
            if key not in base_keys:
                globals().pop(key)

    def get_globals(self) -> dict:
        """Returns globals dict"""

        return globals()

    def execute_macros(self) -> Tuple[str, str]:
        """Executes all macros and returns result string and error string

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
        code_out = io.StringIO()
        code_err = io.StringIO()
        err_msg = io.StringIO()

        # Capture output and errors
        sys.stdout = code_out
        sys.stderr = code_err

        try:
            signal.signal(signal.SIGALRM, self.handler)
            signal.alarm(self.settings.timeout)
        except AttributeError:
            # No POSIX system
            pass

        try:
            exec(self.macros, globals())
            try:
                signal.alarm(0)
            except AttributeError:
                # No POSIX system
                pass

        except Exception:
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

    def _sorted_keys(self, keys: Iterable[Tuple[int, int, int]],
                     startkey: Tuple[int, int, int],
                     reverse: bool = False) -> Iterable[Tuple[int, int, int]]:
        """Generator that yields sorted keys starting with startkey

        :param keys: Key sequence that is sorted
        :param startkey: First key to be yielded
        :param reverse: Sort direction reversed if True

        """

        def tuple_key(tpl):
            return tpl[::-1]

        if reverse:
            def tuple_cmp(tpl):
                return tpl[::-1] > startkey[::-1]
        else:
            def tuple_cmp(tpl):
                return tpl[::-1] < startkey[::-1]

        searchkeys = sorted(keys, key=tuple_key, reverse=reverse)
        searchpos = sum(1 for _ in filter(tuple_cmp, searchkeys))

        searchkeys = searchkeys[searchpos:] + searchkeys[:searchpos]

        for key in searchkeys:
            yield key

    def string_match(self, datastring: str, findstring: str, word: bool,
                     case: bool, regexp: bool) -> int:
        """Returns position of findstring in datastring or None if not found

        :param datastring: String to be searched
        :param findstring: Search string
        :param word: Search full words only if True
        :param case: Search case sensitively if True
        :param regexp: Regular expression search if True

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

        return pos

    def findnextmatch(self, startkey: Tuple[int, int, int], find_string: str,
                      up: bool = False, word: bool = False, case: bool = False,
                      regexp: bool = False, results: bool = True
                      ) -> Tuple[int, int, int]:
        """Returns tuple with position of the next match of find_string or None

        :param startkey: Start position of search
        :param find_string: String to be searched for
        :param up: Search up instead of down if True
        :param word: Search full words only if True
        :param case: Search case sensitively if True
        :param regexp: Regular expression search if True
        :param results: Search includes result string if True (slower)

        """

        def is_matching(key, find_string, word, case, regexp):
            code = self(key)
            pos = self.string_match(code, find_string, word, case, regexp)
            if results:
                if pos is not None:
                    return True
                r_str = str(self[key])
                pos = self.string_match(r_str, find_string, word, case, regexp)
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

    def handler(self, signum: Any, frame: Any):
        """Signal handler for timeout

        :param signum: Ignored
        :param frame: Ignored

        """

        raise RuntimeError("Timeout after {} s.".format(self.settings.timeout))

# End of class CodeArray
