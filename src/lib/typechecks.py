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

Typechecks
==========

typechecks.py contains functions for checking type likeness.

"""


def isslice(obj):
    """Returns True if obj is insatnce of slice"""

    return isinstance(obj, slice)


def isstring(obj):
    """Returns True if obj is instance of str, bytes or bytearray"""

    return isinstance(obj, (str, bytes, bytearray))


def is_svg(code):
    """Checks if code is an svg image

    Parameters
    ----------
    code: String
    \tCode to be parsed in order to check svg complaince

    """

    # The SVG file has to refer to its xmlns
    # Hopefully, it does so wiyhin the first 1000 characters

    if not isinstance(code, bytes):
        return

    code_start = code[:1000]


    if b"http://www.w3.org/2000/svg" in code_start and b"svg" in code_start:
        return True

    return False
