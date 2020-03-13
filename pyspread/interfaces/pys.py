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

pys
===

This file contains interfaces to the native pys file format.

It is split into the following sections

 * shape
 * code
 * attributes
 * row_heights
 * col_widths
 * macros

"""

from builtins import str, map, object

import ast
from base64 import b64decode, b85encode
from collections import OrderedDict

from lib.selection import Selection


def wxcolor2rgb(wxcolor):
    """Returns rtg tuple for given wxPython binary color value"""

    red = wxcolor >> 16
    green = wxcolor - (red << 16) >> 8
    blue = wxcolor - (red << 16) - (green << 8)

    return red, green, blue


wx2qt_fontweights = {
    90: 50,  # wx.FONTWEIGHT_NORMAL
    91: 25,  # wx.FONTWEIGHT_LIGHT
    92: 75,  # wx.FONTWEIGHT_BOLD
    93: 87,  # wx.FONTWEIGHT_MAX
    }

wx2qt_fontstyles = {
    90: 0,  # wx.FONTSTYLE_NORMAL
    93: 1,  # wx.FONTSTYLE_ITALIC
    94: 1,  # wx.FONTSTYLE_SLANT
    95: 2,  # wx.FONTSTYLE_MAX
    }


class PysReader:
    """Reads pys v2.0 file into a code_array"""

    def __init__(self, pys_file, code_array):
        self.pys_file = pys_file
        self.code_array = code_array

        self._section2reader = {
            "[Pyspread save file version]\n": self._pys_version,
            "[shape]\n": self._pys2shape,
            "[grid]\n": self._pys2code,
            "[attributes]\n": self._pys2attributes,
            "[row_heights]\n": self._pys2row_heights,
            "[col_widths]\n": self._pys2col_widths,
            "[macros]\n": self._pys2macros,
        }

        # When converting old versions, cell attributes are rquired that
        # take place after the cell attribute readout
        self.cell_attributes_postfixes = []

    def __iter__(self):
        """Iterates over self.pys_file, replacing everything in code_array"""

        state = None

        # Reset pys_file to start to enable multiple calls of this method
        self.pys_file.seek(0)

        for line in self.pys_file:
            line = line.decode("utf8")
            if line in self._section2reader:
                state = line
            elif state is not None:
                self._section2reader[state](line)
            yield line

        # Apply cell attributes post fixes
        for cell_attribute in self.cell_attributes_postfixes:
            self.code_array.cell_attributes.append(cell_attribute)

    # Decorators

    def version_handler(method):
        """Chooses method`_10` of method if version < 2.0"""

        def new_method(self, *args, **kwargs):
            if self.version <= 1.0:
                method10 = getattr(self, method.__name__+"_10")
                method10(*args, **kwargs)
            else:
                method(self, *args, **kwargs)

        return new_method

    # Helpers

    def _split_tidy(self, string, maxsplit=None):
        """Rstrips string for \n and splits string for \t"""

        if maxsplit is None:
            return string.rstrip("\n").split("\t")
        else:
            return string.rstrip("\n").split("\t", maxsplit)

    def _get_key(self, *keystrings):
        """Returns int key tuple from key string list"""

        return tuple(map(int, keystrings))

    # Sections

    def _pys_version(self, line):
        """pys file version including assertion"""

        self.version = float(line.strip())

        if self.version > 2.0:
            # Abort if file version not supported
            msg = "File version {version} unsupported (> 2.0)."
            raise ValueError(msg.format(version=line.strip()))

    def _pys2shape(self, line):
        """Updates shape in code_array"""

        shape = self._get_key(*self._split_tidy(line))
        if any(dim <= 0 for dim in shape):
            # Abort if any axis is 0 or less
            msg = "Code array has invalid shape {shape}."
            raise ValueError(msg.format(shape=shape))
        self.code_array.shape = shape

    def _code_convert_1_2(self, key, code):
        """Converts chart and image code from v1.0 to v2.0"""

        def get_image_code(image_data, width, height):
            """Returns code string for v2.0"""

            image_buffer_tpl = 'bz2.decompress(base64.b85decode({data}))'
            image_array_tpl = 'numpy.frombuffer({buffer}, dtype="uint8")'
            image_matrix_tpl = '{array}.reshape({height}, {width}, 3)'

            image_buffer = image_buffer_tpl.format(data=image_data)
            image_array = image_array_tpl.format(buffer=image_buffer)
            image_matrix = image_matrix_tpl.format(array=image_array,
                                                   height=height, width=width)

            return image_matrix

        start_str = "bz2.decompress(base64.b64decode('"
        size_start_str = "wx.ImageFromData("
        if size_start_str in code and start_str in code:
            size_start = code.index(size_start_str) + len(size_start_str)
            size_str_list = code[size_start:].split(",")[:2]
            width, height = tuple(map(int, size_str_list))

            # We have a cell that displays a bitmap
            data_start = code.index(start_str) + len(start_str)
            data_stop = code.find("'", data_start)
            enc_data = bytes(code[data_start:data_stop], encoding='utf-8')
            compressed_image_data = b64decode(enc_data)
            reenc_data = b85encode(compressed_image_data)
            code = get_image_code(repr(reenc_data), width, height)

            selection = Selection([], [], [], [], [(key[0], key[1])])
            tab = key[2]
            attrs = {"renderer": "image"}
            self.cell_attributes_postfixes.append((selection, tab, attrs))

        elif "charts.ChartFigure(" in code:
            # We have a matplotlib figure
            selection = Selection([], [], [], [], [(key[0], key[1])])
            tab = key[2]
            attrs = {"renderer": "matplotlib"}
            self.cell_attributes_postfixes.append((selection, tab, attrs))

        return code

    def _pys2code_10(self, line):
        """Updates code in pys code_array - for save file version 1.0"""

        row, col, tab, code = self._split_tidy(line, maxsplit=3)
        key = self._get_key(row, col, tab)

        self.code_array.dict_grid[key] = str(self._code_convert_1_2(key, code))

    @version_handler
    def _pys2code(self, line):
        """Updates code in pys code_array"""

        row, col, tab, code = self._split_tidy(line, maxsplit=3)
        key = self._get_key(row, col, tab)
        self.code_array.dict_grid[key] = ast.literal_eval(code)

    def _attr_convert_1to2(self, key, value):
        """Converts key, value attribute pair from v1.0 to v2.0"""

        color_attrs = ["bordercolor_bottom", "bordercolor_right", "bgcolor",
                       "textcolor"]
        if key in color_attrs:
            return key, wxcolor2rgb(value)

        elif key == "fontweight":
            return key, wx2qt_fontweights[value]

        elif key == "fontstyle":
            return key, wx2qt_fontstyles[value]

        elif key == "markup" and value:
            return "renderer", "markup"

        elif key == "merge_area":
            # Value in v1.0 None if the cell was merged
            # In v 2.0 this is no longer necessary
            return None, value

        # Update justifiaction and alignment values
        elif key in ["vertical_align", "justification"]:
            just_align_value_tansitions = {
                    "left": "justify_left",
                    "center": "justify_center",
                    "right": "justify_right",
                    "top": "align_top",
                    "middle": "align_center",
                    "bottom": "align_bottom",
            }
            return key, just_align_value_tansitions[value]

        return key, value

    def _pys2attributes_10(self, line):
        """Updates attributes in code_array - for save file version 1.0"""

        splitline = self._split_tidy(line)

        selection_data = list(map(ast.literal_eval, splitline[:5]))
        selection = Selection(*selection_data)

        tab = int(splitline[5])

        attrs = {}

        old_merged_cells = {}

        for col, ele in enumerate(splitline[6:]):
            if not (col % 2):
                # Odd entries are keys
                key = ast.literal_eval(ele)

            else:
                # Even cols are values
                value = ast.literal_eval(ele)

                # Convert old wx color values and merged cells
                key_, value_ = self._attr_convert_1to2(key, value)

                if key_ is None and value_ is not None:
                    # We have a merged cell
                    old_merged_cells[value_[:2]] = value_
                try:
                    attrs.pop("merge_area")
                except KeyError:
                    pass
                attrs[key_] = value_

        self.code_array.cell_attributes.append((selection, tab, attrs))

        for key in old_merged_cells:
            selection = Selection([], [], [], [], [key])
            attrs = {"merge_area": old_merged_cells[key]}
            self.code_array.cell_attributes.append((selection, tab, attrs))
        old_merged_cells.clear()

    @version_handler
    def _pys2attributes(self, line):
        """Updates attributes in code_array"""

        splitline = self._split_tidy(line)

        selection_data = list(map(ast.literal_eval, splitline[:5]))
        selection = Selection(*selection_data)

        tab = int(splitline[5])

        attrs = {}

        for col, ele in enumerate(splitline[6:]):
            if not (col % 2):
                # Odd entries are keys
                key = ast.literal_eval(ele)

            else:
                # Even cols are values
                value = ast.literal_eval(ele)
                attrs[key] = value

        self.code_array.cell_attributes.append((selection, tab, attrs))

    def _pys2row_heights(self, line):
        """Updates row_heights in code_array"""

        # Split with maxsplit 3
        split_line = self._split_tidy(line)
        key = row, tab = self._get_key(*split_line[:2])
        height = float(split_line[2])

        shape = self.code_array.shape

        try:
            if row < shape[0] and tab < shape[2]:
                self.code_array.row_heights[key] = height

        except ValueError:
            pass

    def _pys2col_widths(self, line):
        """Updates col_widths in code_array"""

        # Split with maxsplit 3
        split_line = self._split_tidy(line)
        key = col, tab = self._get_key(*split_line[:2])
        width = float(split_line[2])

        shape = self.code_array.shape

        try:
            if col < shape[1] and tab < shape[2]:
                self.code_array.col_widths[key] = width

        except ValueError:
            pass

    def _pys2macros(self, line):
        """Updates macros in code_array"""

        self.code_array.macros += line


class PysWriter(object):
    """Interface between code_array and pys file data

    Iterating over it yields a pys file lines

    Parameters
    ----------

    code_array: model.CodeArray object
    \tThe code_array object data structure

    """

    def __init__(self, code_array):
        self.code_array = code_array

        self.version = 2.0

        self._section2writer = OrderedDict([
            ("[Pyspread save file version]\n", self._version2pys),
            ("[shape]\n", self._shape2pys),
            ("[grid]\n", self._code2pys),
            ("[attributes]\n", self._attributes2pys),
            ("[row_heights]\n", self._row_heights2pys),
            ("[col_widths]\n", self._col_widths2pys),
            ("[macros]\n", self._macros2pys),
        ])

    def __iter__(self):
        """Yields a pys_file line wise from code_array"""

        for key in self._section2writer:
            yield key
            for line in self._section2writer[key]():
                yield line

    def __len__(self):
        """Returns how many lines will be written when saving the code_array"""

        lines = 9  # Headers + 1 line version + 1 line shape
        lines += len(self.code_array.dict_grid)
        lines += len(self.code_array.cell_attributes)
        lines += len(self.code_array.dict_grid.row_heights)
        lines += len(self.code_array.dict_grid.col_widths)
        lines += self.code_array.dict_grid.macros.count('\n')

        return lines

    def _version2pys(self):
        """Writes pys file version to pys file

        Format: <version>\n

        """

        yield repr(self.version) + "\n"

    def _shape2pys(self):
        """Writes shape to pys file

        Format: <rows>\t<cols>\t<tabs>\n

        """

        yield u"\t".join(map(str, self.code_array.shape)) + u"\n"

    def _code2pys(self):
        """Writes code to pys file

        Format: <row>\t<col>\t<tab>\t<code>\n

        """

        for key in self.code_array:
            key_str = u"\t".join(repr(ele) for ele in key)
            if self.version <= 1.0:
                code_str = self.code_array(key)
            else:
                code_str = repr(self.code_array(key))
            out_str = key_str + u"\t" + code_str + u"\n"

            yield out_str

    def _attributes2pys(self):
        """Writes attributes to pys file

        Format:
        <selection[0]>\t[...]\t<tab>\t<key>\t<value>\t[...]\n

        """

        # Remove doublettes
        purged_cell_attributes = []
        purged_cell_attributes_keys = []
        for selection, tab, attr_dict in self.code_array.cell_attributes:
            if purged_cell_attributes_keys and \
               (selection, tab) == purged_cell_attributes_keys[-1]:
                purged_cell_attributes[-1][2].update(attr_dict)
            else:
                purged_cell_attributes_keys.append((selection, tab))
                purged_cell_attributes.append([selection, tab, attr_dict])

        for selection, tab, attr_dict in purged_cell_attributes:
            sel_list = [selection.block_tl, selection.block_br,
                        selection.rows, selection.cols, selection.cells]

            tab_list = [tab]

            attr_dict_list = []
            for key in attr_dict:
                if key is not None:
                    attr_dict_list.append(key)
                    attr_dict_list.append(attr_dict[key])

            line_list = list(map(repr, sel_list + tab_list + attr_dict_list))

            yield u"\t".join(line_list) + u"\n"

    def _row_heights2pys(self):
        """Writes row_heights to pys file

        Format: <row>\t<tab>\t<value>\n

        """

        for row, tab in self.code_array.dict_grid.row_heights:
            if row < self.code_array.shape[0] and \
               tab < self.code_array.shape[2]:
                height = self.code_array.dict_grid.row_heights[(row, tab)]
                height_strings = list(map(repr, [row, tab, height]))
                yield u"\t".join(height_strings) + u"\n"

    def _col_widths2pys(self):
        """Writes col_widths to pys file

        Format: <col>\t<tab>\t<value>\n

        """

        for col, tab in self.code_array.dict_grid.col_widths:
            if col < self.code_array.shape[1] and \
               tab < self.code_array.shape[2]:
                width = self.code_array.dict_grid.col_widths[(col, tab)]
                width_strings = list(map(repr, [col, tab, width]))
                yield u"\t".join(width_strings) + u"\n"

    def _macros2pys(self):
        """Writes macros to pys file

        Format: <macro code line>\n

        """

        macros = self.code_array.dict_grid.macros
        yield macros
