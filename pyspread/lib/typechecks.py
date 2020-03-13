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

Contains functions for checking type likeness.

"""

from io import BytesIO
import xml.etree.ElementTree as ET


def isslice(obj):
    """Returns True if obj is insatnce of slice"""

    return isinstance(obj, slice)


def isstring(obj):
    """Returns True if obj is instance of str, bytes or bytearray"""

    return isinstance(obj, (str, bytes, bytearray))


def is_svg(svg_bytes):
    """Checks if code is an svg image

    Parameters
    ----------
    code: String
    \tCode to be parsed in order to check svg complaince

    """

    tag = None

    svg = BytesIO(svg_bytes)

    try:
        for event, el in ET.iterparse(svg, ('start',)):
            tag = el.tag
            break
    except ET.ParseError:
        pass

    svg.close()

    return tag == '{http://www.w3.org/2000/svg}svg'
