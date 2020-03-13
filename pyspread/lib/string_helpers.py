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

 * :func:`quote`
 * :func:`wrap_text`

"""

import xml.etree.ElementTree as ET
import textwrap


def quote(code):
    """Returns quoted code if not already quoted and if possible

    Parameters
    ----------

    * code: String
    \tCode that is to be quoted

    """

    starts_and_ends = [
        ("'", "'"),
        ('"', '"'),
        ("u'", "'"),
        ('u"', '"'),
        ("b'", "'"),
        ('b"', '"'),
        ("r'", "'"),
        ('r"', '"'),
    ]

    if code is None or not (isinstance(code, bytes) or isinstance(code, str)):
        return code

    code = code.strip()

    if code and not (code[0],  code[-1]) in starts_and_ends:
        return repr(code)
    else:
        return code


def wrap_text(text, width=80, maxlen=2000):
    """Returns wrapped text

    Parameters
    ----------

    * text: String
    \tThe text to bewrapped
    * width: Integer, defaulys to 80
    \tWidth of the text to be wrapped
    * maxlen, defaults to 2000
    \tMaximum total text length before text in truncated and extended by [...]
    \tIf None then truncation is disabled

    """

    if text is None:
        return

    if maxlen is not None and len(text) > maxlen:
        text = text[:maxlen] + "..."
    return "\n".join(textwrap.wrap(text, width=width))


def get_svg_size(svg_bytes):
    """Returns width, height tuple from svg"""

    tree = ET.fromstring(svg_bytes)
    width_str = tree.get("width")
    height_str = tree.get("height")
    width = int(float(''.join(n for n in width_str
                              if n.isdigit() or n == '.')))
    height = int(float(''.join(n for n in height_str
                               if n.isdigit() or n == '.')))
    return width, height
