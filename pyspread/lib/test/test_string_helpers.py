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

**Unit tests for string_helpers.py**

"""

import pytest
from ..string_helpers import quote, wrap_text, get_svg_size


param_test_quote = [
    (None, None),
    (1, 1),
    ("", ""),
    ("Test", "'Test'"),
    ("ü+", "'ü+'"),
    (u"ü+", "'ü+'"),
    (r"ü+", "'ü+'"),
    (b"Test", "b'Test'"),
    ("Test1\nTest2", "'Test1\\nTest2'"),
]


@pytest.mark.parametrize("code, res", param_test_quote)
def test_quote(code, res):
    """Unit test for quote"""

    assert quote(code) == res


param_test_wrap_text = [
    ("", 80, 2000, ""),
    ("."*81, 80, 2000, "."*80+"\n."),
    (r"."*81, 80, 2000, "."*80+"\n."),
    ("~"*81, 80, 2000, "~"*80+"\n~"),
    (u"\u2200"*81, 80, 2000, "\u2200"*80+"\n\u2200"),
    ("."*160, 80, 2000, "."*80+"\n"+"."*80),
    ("x"*160, 80, 2, "xx..."),
    ("."*10, 2, 2000, "\n".join([".."]*5)),
]


@pytest.mark.parametrize("text, width, maxlen, res", param_test_wrap_text)
def test_wrap_text(text, width, maxlen, res):
    """Unit test for wrap_text"""

    assert wrap_text(text, width, maxlen) == res


SVG_1 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   width="218.36047mm"
   height="218.36047mm"
   viewBox="0 0 218.36048 218.36048"
   version="1.1"
   id="svg8"
   inkscape:version="0.92.3 (2405546, 2018-03-11)"
   sodipodi:docname="format-borders-1.svg">
  <defs
     id="defs2" />
  <sodipodi:namedview
     id="base"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageopacity="0.0"
     inkscape:pageshadow="2"
     inkscape:zoom="0.49497476"
     inkscape:cx="-127.83766"
     inkscape:cy="370.91478"
     inkscape:document-units="mm"
     inkscape:current-layer="layer1"
     showgrid="false"
     inkscape:window-width="1280"
     inkscape:window-height="970"
     inkscape:window-x="0"
     inkscape:window-y="0"
     inkscape:window-maximized="1"
     fit-margin-top="0"
     fit-margin-left="0"
     fit-margin-right="0"
     fit-margin-bottom="0" />
  <metadata
     id="metadata5">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title />
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g
     inkscape:label="Layer 1"
     inkscape:groupmode="layer"
     id="layer1"
     transform="translate(12.75978,-2.0734556)">
    <path
       style="fill:none;stroke:#000000;stroke-width:1;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1"
       d="m 27.703878,111.238 137.401542,2e-5"
       id="path846-3-0"
       inkscape:connector-curvature="0" />
  </g>
</svg>
"""


def test_get_svg_size():
    """Unit test for get_svg_size"""

    assert get_svg_size(SVG_1) == (218, 218)
