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

High resolution svg support for qimage and :mod:`matplotlib.figure`

**Provides**

* :class:`QImageSvg`


"""

from io import StringIO

from PyQt5.QtGui import QImage, QPainter
try:
    from PyQt5.QtSvg import QSvgRenderer
except ImportError:
    QSvgRenderer = None

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
except ImportError:
    Figure = None


class QImageSvg(QImage):
    """Subclass of PyQt5.QtGui

    Adds support for SVG byte strings and matplotlib figures

    """

    def from_svg_bytes(self, svg_bytes: bytes):
        """Paints an svg from a bytes object

        :param svg_bytes: SVG file content

        """

        renderer = QSvgRenderer(svg_bytes)
        painter = QPainter(self)
        painter.eraseRect(self.rect())
        renderer.render(painter)
        painter.end()

    def _matplotlib_figure2svg_bytes(self, figure: Figure) -> bytes:
        """Converts a a matplotlib figure to an SVG bytes object

        :param figure: Matplotib figure
        :return: SVG file content

        """

        canvas = FigureCanvasQTAgg(figure)
        svg_filelike = StringIO()
        figure.savefig(svg_filelike, format="svg")
        svg_filelike.seek(0)
        svg_bytes = bytes(svg_filelike.read(), encoding='utf-8')
        svg_filelike.close()

        return svg_bytes

    def from_matplotlib(self, figure: Figure):
        """Paints an svg from a matplotlib figure

        :param figure: Matplotib figure

        """

        if not isinstance(figure, Figure):
            msg_tpl = "figure must be instance of {}."
            msg = msg_tpl.format(Figure)
            raise ValueError(msg)

        svg_bytes = self._matplotlib_figure2svg_bytes(figure)
        self.from_svg_bytes(svg_bytes)
