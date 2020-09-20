#!/usr/bin/env python
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
test_model
==========

Unit tests for model.py

"""
from builtins import zip
from builtins import map
from builtins import str
from builtins import range
from builtins import object

import fractions  # Yes, it is required
import math  # Yes, it is required
from os.path import abspath, dirname, join
import sys

import pytest
import numpy

pyspread_path = abspath(join(dirname(__file__) + "/../.."))
sys.path.insert(0, pyspread_path)

from model.model import (KeyValueStore, CellAttributes, DictGrid, DataArray,
                         CodeArray, CellAttribute, DefaultCellAttributeDict)

from lib.attrdict import AttrDict
from lib.selection import Selection
sys.path.pop(0)


class Settings:
    """Simulates settings class"""

    timeout = 1000


class TestKeyValueStore(object):
    """Unit tests for KeyValueStore"""

    def setup_method(self, method):
        """Creates empty KeyValueStore"""

        self.k_v_store = KeyValueStore()

    def test_missing(self):
        """Test if missing value returns None"""

        key = (1, 2, 3)
        assert self.k_v_store[key] is None

        self.k_v_store[key] = 7

        assert self.k_v_store[key] == 7


class TestCellAttributes(object):
    """Unit tests for CellAttributes"""

    def setup_method(self, method):
        """Creates empty CellAttributes"""

        self.cell_attr = CellAttributes()

    def test_append(self):
        """Test append"""

        selection = Selection([], [], [], [], [(23, 12)])
        table = 0
        attr = AttrDict([("angle", 0.2)])

        self.cell_attr.append(CellAttribute(selection, table, attr))

        # Check if 1 item - the actual action has been added
        assert not self.cell_attr._attr_cache

    def test_getitem(self):
        """Test __getitem__"""

        selection_1 = Selection([(2, 2)], [(4, 5)], [55], [55, 66], [(34, 56)])
        selection_2 = Selection([], [], [], [], [(32, 53), (34, 56)])

        ca1 = CellAttribute(selection_1, 0, AttrDict([("testattr", 3)]))
        ca2 = CellAttribute(selection_2, 0, AttrDict([("testattr", 2)]))

        self.cell_attr.append(ca1)
        self.cell_attr.append(ca2)

        assert self.cell_attr[32, 53, 0].testattr == 2
        assert self.cell_attr[2, 2, 0].testattr == 3

    def test_get_merging_cell(self):
        """Test get_merging_cell"""

        selection_1 = Selection([(2, 2)], [(5, 5)], [], [], [])
        selection_2 = Selection([(3, 2)], [(9, 9)], [], [], [])
        selection_3 = Selection([(2, 2)], [(9, 9)], [], [], [])

        attr_dict_1 = AttrDict([("merge_area", (2, 2, 5, 5))])
        attr_dict_2 = AttrDict([("merge_area", (3, 2, 9, 9))])
        attr_dict_3 = AttrDict([("merge_area", (2, 2, 9, 9))])

        cell_attribute_1 = CellAttribute(selection_1, 0, attr_dict_1)
        cell_attribute_2 = CellAttribute(selection_2, 0, attr_dict_2)
        cell_attribute_3 = CellAttribute(selection_3, 1, attr_dict_3)

        self.cell_attr.append(cell_attribute_1)
        self.cell_attr.append(cell_attribute_2)
        self.cell_attr.append(cell_attribute_3)

        # Cell 1. 1, 0 is not merged
        assert self.cell_attr.get_merging_cell((1, 1, 0)) is None

        # Cell 3. 3, 0 is merged to cell 3, 2, 0
        assert self.cell_attr.get_merging_cell((3, 3, 0)) == (2, 2, 0)

        # Cell 2. 2, 0 is merged to cell 2, 2, 0
        assert self.cell_attr.get_merging_cell((2, 2, 0)) == (2, 2, 0)


class TestDictGrid(object):
    """Unit tests for DictGrid"""

    def setup_method(self, method):
        """Creates empty DictGrid"""

        self.dict_grid = DictGrid((100, 100, 100))

    def test_getitem(self):
        """Unit test for __getitem__"""

        with pytest.raises(IndexError):
            self.dict_grid[100, 0, 0]

        self.dict_grid[(2, 4, 5)] = "Test"
        assert self.dict_grid[(2, 4, 5)] == "Test"


class TestDataArray(object):
    """Unit tests for DataArray"""

    def setup_method(self, method):
        """Creates empty DataArray"""

        self.data_array = DataArray((100, 100, 100), Settings())

    def test_iter(self):
        """Unit test for __iter__"""

        assert list(iter(self.data_array)) == []

        self.data_array[(1, 2, 3)] = "12"
        self.data_array[(1, 2, 4)] = "13"

        assert sorted(list(iter(self.data_array))) == [(1, 2, 3), (1, 2, 4)]

    def test_keys(self):
        """Unit test for keys"""

        assert list(self.data_array.keys()) == []

        self.data_array[(1, 2, 3)] = "12"
        self.data_array[(1, 2, 4)] = "13"

        assert sorted(self.data_array.keys()) == [(1, 2, 3), (1, 2, 4)]

    def test_pop(self):
        """Unit test for pop"""

        self.data_array[(1, 2, 3)] = "12"
        self.data_array[(1, 2, 4)] = "13"

        assert self.data_array.pop((1, 2, 3)) == "12"

        assert sorted(self.data_array.keys()) == [(1, 2, 4)]

    def test_get_shape(self):
        """Unit test for _get_shape"""

        assert self.data_array.shape == (100, 100, 100)

    def test_set_shape(self):
        """Unit test for _set_shape"""

        self.data_array.shape = (10000, 100, 100)
        assert self.data_array.shape == (10000, 100, 100)

    param_get_last_filled_cell = [
        ({(0, 0, 0): "2"}, 0, (0, 0)),
        ({(2, 0, 2): "2"}, 0, (0, 0)),
        ({(2, 0, 2): "2"}, None, (2, 0)),
        ({(2, 0, 2): "2"}, 2, (2, 0)),
        ({(32, 30, 0): "432"}, 0, (32, 30)),
    ]

    @pytest.mark.parametrize("content,table,res", param_get_last_filled_cell)
    def test_get_last_filled_cell(self, content, table, res):
        """Unit test for get_last_filled_cellet_end"""

        for key in content:
            self.data_array[key] = content[key]

        assert self.data_array.get_last_filled_cell(table)[:2] == res

    def test_getstate(self):
        """Unit test for __getstate__ (pickle support)"""

        assert "dict_grid" in self.data_array.__getstate__()

    def test_slicing(self):
        """Unit test for __getitem__ and __setitem__"""

        self.data_array[0, 0, 0] = "'Test'"
        self.data_array[0, 0, 0] = "'Tes'"

        assert self.data_array[0, 0, 0] == "'Tes'"

    def test_cell_array_generator(self):
        """Unit test for cell_array_generator"""

        cell_array = self.data_array[:5, 0, 0]

        assert list(cell_array) == [None] * 5

        cell_array = self.data_array[:5, :5, 0]

        assert [list(c) for c in cell_array] == [[None] * 5] * 5

        cell_array = self.data_array[:5, :5, :5]

        assert [[list(e) for e in c] for c in cell_array] == \
            [[[None] * 5] * 5] * 5

    param_adjust_rowcol = [
        ({(0, 0): 3.0}, 0, 2, 0, 0, (0, 0), 3.0),
        ({(0, 0): 3.0}, 0, 2, 0, 0, (2, 0), 3.0),
        ({(0, 0): 3.0}, 0, 1, 1, 0, (1, 0), 3.0),
        ({(0, 0): 3.0}, 0, 1, 1, 0, (0, 1), 0.0),
    ]

    @pytest.mark.parametrize("vals, ins_point, no2ins, axis, tab, target, res",
                             param_adjust_rowcol)
    def test_adjust_rowcol(self, vals, ins_point, no2ins, axis, tab, target,
                           res):
        """Unit test for _adjust_rowcol"""

        if axis == 0:
            __vals = self.data_array.row_heights
        elif axis == 1:
            __vals = self.data_array.col_widths
        else:
            raise ValueError("{} out of 0, 1".format(axis))

        __vals.update(vals)

        self.data_array._adjust_rowcol(ins_point, no2ins, axis, tab)
        assert __vals[target] == res

    def test_set_cell_attributes(self):
        """Unit test for _set_cell_attributes"""

        cell_attributes = self.data_array.cell_attributes

        attr = CellAttribute(Selection([], [], [], [], []), 0,
                             AttrDict([("Test", None)]))
        cell_attributes.clear()
        cell_attributes.append(attr)

        assert self.data_array.cell_attributes == cell_attributes

    param_adjust_cell_attributes = [
        (0, 5, 0, (4, 3, 0), (9, 3, 0)),
        (34, 5, 0, (4, 3, 0), (4, 3, 0)),
        (0, 0, 0, (4, 3, 0), (4, 3, 0)),
        (1, 5, 1, (4, 3, 0), (4, 8, 0)),
        (1, 5, 1, (4, 3, 1), (4, 8, 1)),
        (0, -1, 2, (4, 3, 1), None),
        (0, -1, 2, (4, 3, 2), (4, 3, 1)),
    ]

    @pytest.mark.parametrize("inspoint, noins, axis, src, target",
                             param_adjust_cell_attributes)
    def test_adjust_cell_attributes(self, inspoint, noins, axis, src, target):
        """Unit test for _adjust_cell_attributes"""

        row, col, tab = src

        cell_attributes = self.data_array.cell_attributes

        attr_dict = AttrDict([("angle", 0.2)])
        attr = CellAttribute(Selection([], [], [], [], [(row, col)]), tab,
                             attr_dict)
        cell_attributes.clear()
        cell_attributes.append(attr)

        self.data_array._adjust_cell_attributes(inspoint, noins, axis)

        if target is None:
            for key in attr_dict:
                # Should be at default value
                default_ca = DefaultCellAttributeDict()[key]
                assert cell_attributes[src][key] == default_ca
        else:
            for key in attr_dict:
                assert cell_attributes[target][key] == attr_dict[key]

    param_test_insert = [
        ({(2, 3, 0): "42"}, 1, 1, 0, None,
         {(2, 3, 0): None, (3, 3, 0): "42"}),
        ({(0, 0, 0): "0", (0, 0, 2): "2"}, 1, 1, 2, None,
         {(0, 0, 3): "2", (0, 0, 4): None}),
    ]

    @pytest.mark.parametrize("data, inspoint, notoins, axis, tab, res",
                             param_test_insert)
    def test_insert(self, data, inspoint, notoins, axis, tab, res):
        """Unit test for insert operation"""

        self.data_array.dict_grid.update(data)
        self.data_array.insert(inspoint, notoins, axis, tab)

        for key in res:
            assert self.data_array[key] == res[key]

    param_test_delete = [
        ({(2, 3, 4): "42"}, 1, 1, 0, None, {(1, 3, 4): "42"}),
        ({(0, 0, 0): "1"}, 0, 1, 0, 0, {(0, 0, 0): None}),
        ({(0, 0, 1): "1"}, 0, 1, 2, None, {(0, 0, 0): "1"}),
        ({(3, 3, 2): "3"}, 0, 2, 2, None, {(3, 3, 0): "3"}),
        ({(4, 2, 1): "3"}, 2, 1, 1, 1, {(4, 2, 1): None}),
        ({(10, 0, 0): "1"}, 0, 10, 0, 0, {(0, 0, 0): "1"}),
    ]

    @pytest.mark.parametrize("data, delpoint, notodel, axis, tab, res",
                             param_test_delete)
    def test_delete(self, data, delpoint, notodel, axis, tab, res):
        """Tests delete operation"""

        self.data_array.dict_grid.update(data)
        self.data_array.delete(delpoint, notodel, axis, tab)

        for key in res:
            assert self.data_array[key] == res[key]

    def test_delete_error(self):
        """Tests delete operation error"""

        self.data_array[2, 3, 4] = "42"

        try:
            self.data_array.delete(1, 1, 20)
            assert False
        except ValueError:
            pass

    def test_set_row_height(self):
        """Unit test for set_row_height"""

        self.data_array.set_row_height(7, 1, 22.345)
        assert self.data_array.row_heights[7, 1] == 22.345

    def test_set_col_width(self):
        """Unit test for set_col_width"""

        self.data_array.set_col_width(7, 1, 22.345)
        assert self.data_array.col_widths[7, 1] == 22.345


class TestCodeArray(object):
    """Unit tests for CodeArray"""

    def setup_method(self, method):
        """Creates empty DataArray"""

        self.code_array = CodeArray((100, 10, 3), Settings())

    param_test_setitem = [
        ({(2, 3, 2): "42"}, {(1, 3, 2): "42"},
         {(1, 3, 2): "42", (2, 3, 2): "42"}),
    ]

    @pytest.mark.parametrize("data, items, res_data", param_test_setitem)
    def test_setitem(self, data, items, res_data):
        """Unit test for __setitem__"""

        self.code_array.dict_grid.update(data)
        for key in items:
            self.code_array[key] = items[key]
        for key in res_data:
            assert res_data[key] == self.code_array(key)

    def test_slicing(self):
        """Unit test for __getitem__ and __setitem__"""

        # Test for item getting, slicing, basic evaluation correctness

        shape = self.code_array.shape
        x_list = [0, shape[0]-1]
        y_list = [0, shape[1]-1]
        z_list = [0, shape[2]-1]
        for x, y, z in zip(x_list, y_list, z_list):
            assert self.code_array[x, y, z] is None
            self.code_array[:x, :y, :z]
            self.code_array[:x:2, :y:2, :z:-1]

        get_shape = numpy.array(self.code_array[:, :, :]).shape
        orig_shape = self.code_array.shape
        assert get_shape == orig_shape

        gridsize = 100
        filled_grid = CodeArray((gridsize, 10, 1), Settings())
        for i in [-2**99, 2**99, 0]:
            for j in range(gridsize):
                filled_grid[j, 0, 0] = str(i)
                filled_grid[j, 1, 0] = str(i) + '+' + str(j)
                filled_grid[j, 2, 0] = str(i) + '*' + str(j)

            for j in range(gridsize):
                assert filled_grid[j, 0, 0] == i
                assert filled_grid[j, 1, 0] == i + j
                assert filled_grid[j, 2, 0] == i * j

            for j, funcname in enumerate(['int', 'math.ceil',
                                          'fractions.Fraction']):
                filled_grid[0, 0, 0] = "fractions = __import__('fractions')"
                filled_grid[0, 0, 0]
                filled_grid[1, 0, 0] = "math = __import__('math')"
                filled_grid[1, 0, 0]
                filled_grid[j, 3, 0] = funcname + ' (' + str(i) + ')'

                assert filled_grid[j, 3, 0] == eval(funcname + "(" + "i" + ")")
        # Test X, Y, Z
        for i in range(10):
            self.code_array[i, 0, 0] = str(i)
        assert [self.code_array((i, 0, 0)) for i in range(10)] == \
            list(map(str, range(10)))

        assert [self.code_array[i, 0, 0] for i in range(10)] == list(range(10))

        # Test cycle detection

        filled_grid[0, 0, 0] = "numpy.arange(0, 10, 0.1)"
        filled_grid[1, 0, 0] = "sum(S[0,0,0])"

        assert filled_grid[1, 0, 0] == sum(numpy.arange(0, 10, 0.1))

    def test_make_nested_list(self):
        """Unit test for _make_nested_list"""

        def gen():
            """Nested generator"""

            yield (("Test" for _ in range(2)) for _ in range(2))

        res = self.code_array._make_nested_list(gen())

        assert res == [[["Test" for _ in range(2)] for _ in range(2)]]

    data_eval_cell = [
        ((0, 0, 0), "2 + 4", 6),
        ((1, 0, 0), "S[0, 0, 0]", None),
        ((43, 2, 1), "X, Y, Z", (43, 2, 1)),
    ]

    @pytest.mark.parametrize("key, code, res", data_eval_cell)
    def test_eval_cell(self, key, code, res):
        """Unit test for _eval_cell"""

        self.code_array[key] = code
        assert self.code_array._eval_cell(key, code) == res

    def test_execute_macros(self):
        """Unit test for execute_macros"""

        self.code_array.macros = "a = 5\ndef f(x): return x ** 2"
        self.code_array.execute_macros()
        assert self.code_array._eval_cell((0, 0, 0), "a") == 5
        assert self.code_array._eval_cell((0, 0, 0), "f(2)") == 4

    def test_sorted_keys(self):
        """Unit test for _sorted_keys"""

        code_array = self.code_array

        keys = [(1, 0, 0), (2, 0, 0), (0, 1, 0), (0, 99, 0), (0, 0, 0),
                (0, 0, 99), (1, 2, 3)]
        sorted_keys = [(0, 1, 0), (0, 99, 0), (1, 2, 3), (0, 0, 99), (0, 0, 0),
                       (1, 0, 0), (2, 0, 0)]
        rev_sorted_keys = [(0, 1, 0), (2, 0, 0), (1, 0, 0), (0, 0, 0),
                           (0, 0, 99), (1, 2, 3), (0, 99, 0)]

        sort_gen = code_array._sorted_keys(keys, (0, 1, 0))
        for result, expected_result in zip(sort_gen, sorted_keys):
            assert result == expected_result

        rev_sort_gen = code_array._sorted_keys(keys, (0, 3, 0), reverse=True)
        for result, expected_result in zip(rev_sort_gen, rev_sorted_keys):
            assert result == expected_result

    def test_string_match(self):
        """Tests creation of string_match"""

        code_array = self.code_array

        test_strings = [
            "", "Hello", " Hello", "Hello ", " Hello ", "Hello\n",
            "THelloT", " HelloT", "THello ", "hello", "HELLO", "sd"
        ]

        search_string = "Hello"

        # Normal search
        flags = False, False, False
        results = [None, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, None]
        for test_string, result in zip(test_strings, results):
            res = code_array.string_match(test_string, search_string, *flags)
            assert res == result

        # Case sensitive
        flags = False, True, False
        results = [None, 0, 1, 0, 1, 0, 1, 1, 1, None, None, None]
        for test_string, result in zip(test_strings, results):
            res = code_array.string_match(test_string, search_string, *flags)
            assert res == result

        # Word search
        flags = True, False, False
        results = [None, 0, 1, 0, 1, 0, None, None, None, 0, 0, None]
        for test_string, result in zip(test_strings, results):
            res = code_array.string_match(test_string, search_string, *flags)
            assert res == result

    def test_findnextmatch(self):
        """Find method test"""

        code_array = self.code_array

        for i in range(100):
            code_array[i, 0, 0] = str(i)

        assert code_array[3, 0, 0] == 3
        assert code_array.findnextmatch((0, 0, 0), "3", False) == (3, 0, 0)
        assert code_array.findnextmatch((0, 0, 0), "99", True) == (99, 0, 0)
