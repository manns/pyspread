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

 * :class:`ProgressDialogCanceled`
 * :func:`progress_dialog`
 * :func:`linecount`
 * :func:`file_progress_gen`

"""

from contextlib import contextmanager
from functools import partial
from typing import BinaryIO, ContextManager, Generator, IO, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressDialog


class ProgressDialogCanceled(Exception):
    """Raised when a progress dialog is canceled"""

    pass


@contextmanager
def progress_dialog(main_window: QMainWindow, title: str, label: str,
                    maximum: int) -> ContextManager[QProgressDialog]:
    """:class:`~contextlib.contextmanager` that displays a progress dialog

    :param main_window: Application main window
    :param title: Progress dialog title
    :param label: Progress dialog label
    :param maximum: Maximum value for progress

    """

    progress_dialog = QProgressDialog(main_window)
    progress_dialog.setWindowTitle(title)
    progress_dialog.setWindowModality(Qt.WindowModal)
    progress_dialog.setLabelText(label)
    progress_dialog.setMaximum(maximum)

    yield progress_dialog

    progress_dialog.setValue(maximum)
    progress_dialog.close()
    progress_dialog.deleteLater()


def linecount(infile: BinaryIO, buffer_size: int = 1024*1024) -> int:
    """Count lines in infile

    Starts at current position in file. Position is not preserved.
    Idea taken from https://stackoverflow.com/questions/845058

    :param infile: File like object for which lines are counted (binary mode!)
    :param buffer_size: Buffer size for reading the file
    :return: Number of newlines in infile

    """

    buffer_gen = iter(partial(infile.raw.read, buffer_size), b'')
    return sum(buffer.count(b'\n') for buffer in buffer_gen)


def file_progress_gen(main_window, file: IO, title: str, label: str,
                      no_lines: int, step: int = 100) \
                      -> Generator[Tuple[int, str], None, None]:
    """A generator for file iteration that displays a progress bar

    Yields (line number, line string).
    Return value on user cancel via progress dialog is current line number

    :param main_window: Application main window
    :param file: File to be iterater over
    :param title: Progress dialog title
    :param label: Progress dialog label
    :param no_lines: Number of lines that are remaining in file
    :param step: Number of lines per progress bar update

    """

    with progress_dialog(main_window, title, label, no_lines) as progress_dlg:
        try:
            for i, line in enumerate(file):
                yield i, line

                if not i % step:
                    progress_dlg.setValue(i)
                    QApplication.instance().processEvents()
                    if progress_dlg.wasCanceled():
                        msg = "File operation canceled at line {}.".format(i)
                        raise ProgressDialogCanceled(msg)
        except GeneratorExit:  # Catch for cleaning up with progress_dialog
            pass
        except Exception as error:
            main_window.grid.model.reset()
            main_window.statusBar().showMessage(str(error))
