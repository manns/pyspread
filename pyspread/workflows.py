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

Workflows for pyspread

"""

from ast import literal_eval
from base64 import b85encode
import bz2
from contextlib import contextmanager
from copy import deepcopy
import csv
from itertools import cycle
import io
from itertools import takewhile, repeat
import os.path
from pathlib import Path
from shutil import move
from tempfile import NamedTemporaryFile

from PyQt5.QtCore \
    import Qt, QMimeData, QModelIndex, QBuffer, QRect, QRectF, QSize
from PyQt5.QtGui import QTextDocument, QImage, QPainter, QBrush, QPen
from PyQt5.QtWidgets \
    import (QApplication, QProgressDialog, QMessageBox, QInputDialog,
            QStyleOptionViewItem)
try:
    from PyQt5.QtSvg import QSvgGenerator
except ImportError:
    QSvgGenerator = None

try:
    import matplotlib.figure as matplotlib_figure
except ImportError:
    matplotlib_figure = None

import commands
from dialogs \
    import (DiscardChangesDialog, FileOpenDialog, GridShapeDialog,
            FileSaveDialog, ImageFileOpenDialog, ChartDialog, CellKeyDialog,
            FindDialog, ReplaceDialog, CsvFileImportDialog, CsvImportDialog,
            CsvExportDialog, CsvExportAreaDialog, CsvFileExportDialog,
            SvgExportAreaDialog)
from interfaces.pys import PysReader, PysWriter
from lib.hashing import sign, verify
from lib.selection import Selection
from lib.typechecks import is_svg
from lib.csv import csv_reader, convert


class Workflows:
    def __init__(self, main_window):
        self.main_window = main_window

    @contextmanager
    def progress_dialog(self, title, label, maximum):
        """:class:`~contextlib.contextmanager` that displays a progress dialog
        """

        progress_dialog = QProgressDialog(self.main_window)
        progress_dialog.setWindowTitle(title)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setLabelText(label)
        progress_dialog.setMaximum(maximum)

        yield progress_dialog

        progress_dialog.setValue(maximum)
        progress_dialog.close()
        progress_dialog.deleteLater()

    @contextmanager
    def disable_entryline_updates(self):
        """:class:`~contextlib.contextmanager` that temporarily disables the
        :class:`entryline.Entryline`

        """

        self.main_window.entry_line.setUpdatesEnabled(False)
        yield
        self.main_window.entry_line.setUpdatesEnabled(True)

    @contextmanager
    def busy_cursor(self):
        """:class:`~contextlib.contextmanager` that displays a busy cursor"""

        QApplication.setOverrideCursor(Qt.WaitCursor)
        yield
        QApplication.restoreOverrideCursor()

    def handle_changed_since_save(func, *args, **kwargs):
        """Decorator to handle changes since last saving the document

        If changes are present then a dialog is displayed that asks if the
        changes shall be discarded.

        - If the user selects `Cancel` then `func` is not executed.
        - If the user selects `Save` then the file is saved and `func` is
          executed.
        - If the user selects `Discard` then the file is not saved and `func`
          is executed.

        If no changes are present then `func` is directly executed.
        After executing `func`, :func:`reset_changed_since_save` and
        `update_main_window_title` are called.

        """

        def function_wrapper(self, *args, **kwargs):
            """Check changes and display and handle the dialog"""

            if self.main_window.settings.changed_since_save:
                choice = DiscardChangesDialog(self.main_window).choice
                if choice is None:
                    return
                elif not choice:
                    # We try to save to a file
                    if self.file_save() is False:
                        # File could not be saved --> Abort
                        return
            try:
                func(self, *args, **kwargs)
            except TypeError:
                func(self)  # No args accepted
            self.reset_changed_since_save()
            self.update_main_window_title()

        return function_wrapper

    def reset_changed_since_save(self):
        """Sets changed_since_save to False and updates the window title"""

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

    def update_main_window_title(self):
        """Change the main window title to reflect the current file name"""

        # Get the current filepath
        filepath = self.main_window.settings.last_file_input_path
        if filepath == Path.home():
            title = "pyspread"
        else:
            title = "{filename} - pyspread".format(filename=filepath.name)
        self.main_window.setWindowTitle(title)

    @handle_changed_since_save
    def file_new(self):
        """File new workflow"""

        maxshape = self.main_window.settings.maxshape

        # Get grid shape from user
        old_shape = self.main_window.grid.model.code_array.shape
        shape = GridShapeDialog(self.main_window, old_shape).shape
        if shape is None:
            # Abort changes because the dialog has been canceled
            return
        elif any(ax == 0 for ax in shape):
            msg = "Invalid grid shape {}.".format(shape)
            self.main_window.statusBar().showMessage(msg)
            return
        elif any(ax > axmax for axmax, ax in zip(maxshape, shape)):
            msg = "Grid shape {} exceeds {}.".format(shape, maxshape)
            self.main_window.statusBar().showMessage(msg)
            return

        # Set current cell to upper left corner
        self.main_window.grid.current = 0, 0, 0

        # Reset grid
        self.main_window.grid.model.reset()

        # Delete old filepath
        self.main_window.settings.last_file_input_path = Path.home()

        # Set new shape
        self.main_window.grid.model.shape = shape

        # Select upper left cell because initial selection behaves strange
        self.main_window.grid.reset_selection()

        # Update cell spans and zoom because this is unsupported by the model
        with self.main_window.grid.undo_resizing_row():
            with self.main_window.grid.undo_resizing_column():
                self.main_window.grid.update_cell_spans()
                self.main_window.grid.update_zoom()

        # Update index widgets
        self.main_window.grid.update_index_widgets()

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

        # Update macro editor
        self.main_window.macro_panel.update()

        # Exit safe mode
        self.main_window.safe_mode = False

    def _get_filesize(self, filepath):
        """Returns the filesize"""

        try:
            filesize = os.path.getsize(filepath)
        except OSError as err:
            msg_tpl = "Error opening file {filepath}: {err}."
            msg = msg_tpl.format(filepath=filepath, err=err)
            self.main_window.statusBar().showMessage(msg)
            return
        return filesize

    def filepath_open(self, filepath):
        """Workflow for opening a file if a filepath is known"""

        grid = self.main_window.grid
        code_array = grid.model.code_array

        filesize = self._get_filesize(filepath)
        if filesize is None:
            return

        # Reset grid
        grid.model.reset()

        # Reset macro editor
        self.main_window.macro_panel.macro_editor.clear()

        # Is the file signed properly ?
        self.main_window.safe_mode = True
        signature_key = self.main_window.settings.signature_key
        try:
            with open(filepath, "rb") as infile:
                signature_path = filepath.with_suffix(filepath.suffix + '.sig')
                with open(signature_path, "rb") as sigfile:
                    self.main_window.safe_mode = not verify(infile.read(),
                                                            sigfile.read(),
                                                            signature_key)
        except OSError:
            self.main_window.safe_mode = True

        # File compression handling
        if filepath.suffix == ".pysu":
            fopen = open
        else:
            fopen = bz2.open

        # Process events before showing the modal progress dialog
        self.main_window.application.processEvents()

        # Load file into grid
        try:
            with fopen(filepath, "rb") as infile:
                title = "File open progress"
                label = "Opening {}...".format(filepath.name)
                with self.progress_dialog(title, label,
                                          filesize) as progress_dialog:
                    try:
                        for line in PysReader(infile, code_array):
                            progress_dialog.setValue(infile.tell())
                            self.main_window.application.processEvents()
                            if progress_dialog.wasCanceled():
                                grid.model.reset()
                                self.main_window.safe_mode = False
                                break
                    except ValueError as error:
                        grid.model.reset()
                        self.main_window.statusBar().showMessage(str(error))
                        progress_dialog.close()
                        return
        except OSError as err:
            msg_tpl = "Error opening file {filepath}: {err}."
            msg = msg_tpl.format(filepath=filepath, err=err)
            self.main_window.statusBar().showMessage(msg)
            # Reset grid
            grid.model.reset()
            return
        # Explicitly set the grid shape
        shape = code_array.shape
        grid.model.shape = shape

        # Update cell spans and zoom because this is unsupported by the model
        with self.main_window.grid.undo_resizing_row():
            with self.main_window.grid.undo_resizing_column():
                self.main_window.grid.update_cell_spans()
                self.main_window.grid.update_zoom()

        # Update index widgets
        grid.update_index_widgets()

        # Select upper left cell because initial selection behaves strangely
        grid.reset_selection()

        # Change the main window last input directory state
        self.main_window.settings.last_file_input_path = filepath

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

        # Update macro editor
        self.main_window.macro_panel.update()

        # Add to file history
        self.main_window.settings.add_to_file_history(filepath.as_posix())

        return filepath

    @handle_changed_since_save
    def file_open(self):
        """File open workflow"""

        if self.main_window.unit_test:
            # We are in a unit test and use the unit test filepath
            filepath = self.main_window.unit_test_data

        else:
            # Get filepath from user
            dial = FileOpenDialog(self.main_window)
            if not dial.file_path:
                return  # Cancel pressed
            filepath = Path(dial.file_path).with_suffix(dial.suffix)

        self.filepath_open(filepath)

    @handle_changed_since_save
    def file_open_recent(self, filepath):
        """File open recent workflow"""

        self.filepath_open(Path(filepath))

    def sign_file(self, filepath):
        """Signs filepath if not in :attr:`model.model.DataArray.safe_mode`"""

        if self.main_window.safe_mode:
            msg = "File saved but not signed because it is unapproved."
            self.main_window.statusBar().showMessage(msg)
            return

        signature_key = self.main_window.settings.signature_key
        try:
            with open(filepath, "rb") as infile:
                signature = sign(infile.read(), signature_key)
        except OSError as err:
            msg = "Error signing file: {}".format(err)
            self.main_window.statusBar().showMessage(msg)
            return

        if signature is None or not signature:
            msg = 'Error signing file. '
            self.main_window.statusBar().showMessage(msg)
            return

        signature_path = filepath.with_suffix(filepath.suffix + '.sig')
        try:
            with open(signature_path, 'wb') as signfile:
                signfile.write(signature)
                msg = "File saved and signed."
        except OSError as err:
            msg_tpl = "Error signing file {filepath}: {err}."
            msg = msg_tpl.format(filepath=filepath, err=err)

        self.main_window.statusBar().showMessage(msg)

    def _save(self, filepath):
        """Save filepath using chosen_filter

        Compresses save file if filepath.suffix is `.pys`

        Parameters
        ----------
        * filepath: pathlib.Path
        \tSave file path

        """

        code_array = self.main_window.grid.model.code_array

        # Process events before showing the modal progress dialog
        self.main_window.application.processEvents()

        # Save grid to temporary file
        with NamedTemporaryFile(delete=False) as tempfile:
            filename = tempfile.name
            try:
                pys_writer = PysWriter(code_array)
                with self.progress_dialog("File save progress",
                                          "Saving {}...".format(filepath.name),
                                          len(pys_writer)) as progress_dialog:
                    for i, line in enumerate(pys_writer):
                        line = bytes(line, "utf-8")
                        if filepath.suffix == ".pys":
                            line = bz2.compress(line)
                        tempfile.write(line)
                        progress_dialog.setValue(i)
                        self.main_window.application.processEvents()
                        if progress_dialog.wasCanceled():
                            tempfile.delete = True  # Delete incomplete tmpfile
                            return
            except (OSError, ValueError) as err:
                tempfile.delete = True
                QMessageBox.critical(self.main_window, "Error saving file",
                                     str(err))
                return
        try:
            if filepath.exists() and not os.access(filepath, os.W_OK):
                raise PermissionError("No write access to {}".format(filepath))
            move(filename, filepath)

        except OSError as err:
            # No tmp file present
            QMessageBox.critical(self.main_window, "Error saving file",
                                 str(err))
            return

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

        # Set the current filepath
        self.main_window.settings.last_file_input_path = filepath

        # Change the main window title
        window_title = "{filename} - pyspread".format(filename=filepath.name)
        self.main_window.setWindowTitle(window_title)

        self.sign_file(filepath)

    def file_save(self):
        """File save workflow"""

        filepath = self.main_window.settings.last_file_input_path
        if filepath.suffix:
            self._save(filepath)

        # New, changed file that has never been saved before
        elif self.file_save_as() is False:
            # Now the user has aborted the file save as dialog
            return False

    def file_save_as(self):
        """File save as workflow"""

        # Get filepath from user
        dial = FileSaveDialog(self.main_window)
        if not dial.file_path:
            return False  # Cancel pressed

        fp = Path(dial.file_path)

        # Extend filepath suffix if needed
        if fp.suffix != dial.suffix:
            fp = fp.with_suffix(dial.suffix)

        self._save(fp)

    def file_import(self):
        """Import csv files"""

        def rawincount(filepath):
            """Counts lines of file"""

            with open(filepath, 'rb') as f:
                bufgen = takewhile(lambda x: x, (f.raw.read(1024*1024)
                                                 for _ in repeat(None)))
                return sum(buf.count(b'\n') for buf in bufgen)

        if self.main_window.unit_test:
            # We are in a unit test and use the unit test filepath
            filepath = self.main_window.unit_test_data

        else:
            # Get filepath from user
            dial = CsvFileImportDialog(self.main_window)
            if not dial.file_path:
                return  # Cancel pressed
            filepath = Path(dial.file_path)

        csv_dlg = CsvImportDialog(self.main_window, filepath)

        if not csv_dlg.exec():
            return

        # Dialog accepted, now fill the grid

        row, column, table = current = self.main_window.grid.current
        model = self.main_window.grid.model
        rows, columns, tables = model.shape

        description_tpl = "Import from csv file {} at cell {}"
        description = description_tpl.format(filepath, current)

        try:
            filelines = rawincount(filepath)
        except OSError as error:
            self.main_window.statusBar().showMessage(str(error))
            return

        command = None

        try:
            with open(filepath, newline='') as csvfile:
                title = "csv import progress"
                label = "Importing {}...".format(filepath.name)
                with self.progress_dialog(title, label,
                                          filelines) as progress_dialog:
                    try:
                        # Enter safe mode
                        self.main_window.safe_mode = True

                        reader = csv_reader(csvfile, csv_dlg.dialect,
                                            csv_dlg.digest_types)
                        for i, line in enumerate(reader):
                            if row + i >= rows:
                                break
                            if i % 100 == 0:
                                progress_dialog.setValue(i)
                                self.main_window.application.processEvents()
                                if progress_dialog.wasCanceled():
                                    return

                            for j, ele in enumerate(line):
                                if column + j >= columns:
                                    break

                                if csv_dlg.digest_types is None:
                                    code = str(ele)
                                else:
                                    code = convert(ele,
                                                   csv_dlg.digest_types[j])
                                index = model.index(row + i, column + j)
                                cmd = commands.SetCellCode(code, model, index,
                                                           description)

                                if command is None:
                                    command = cmd
                                else:
                                    command.mergeWith(cmd)
                    except ValueError as error:
                        msg = str(error)
                        self.main_window.statusBar().showMessage(msg)
                        return

                    self.main_window.undo_stack.push(command)
        except OSError as error:
            self.main_window.statusBar().showMessage(str(error))
            return

    def file_export(self):
        """Export csv and svg files"""

        # Get filepath from user
        dial = CsvFileExportDialog(self.main_window)
        if not dial.file_path:
            return  # Cancel pressed
        filepath = Path(dial.file_path)

        if "CSV" in dial.selected_filter:
            self._csv_export(filepath)
        elif "SVG" in dial.selected_filter:
            # Extend filepath suffix if needed
            if filepath.suffix != dial.suffix:
                filepath = filepath.with_suffix(dial.suffix)
            self._svg_export(filepath)

    def _csv_export(self, filepath):
        """Export to csv file filepath"""

        # Get area for csv export
        csv_area = CsvExportAreaDialog(self.main_window,
                                       self.main_window.grid).area
        if csv_area is None:
            return

        top, left, bottom, right = csv_area
        code_array = self.main_window.grid.model.code_array
        table = self.main_window.grid.table
        csv_data = code_array[top: bottom + 1, left: right + 1, table]

        csv_dlg = CsvExportDialog(self.main_window, csv_area)

        if not csv_dlg.exec():
            return

        try:
            with open(filepath, "w", newline='') as csvfile:
                writer = csv.writer(csvfile, dialect=csv_dlg.dialect)
                writer.writerows(csv_data)
        except OSError as error:
            self.main_window.statusBar().showMessage(str(error))

    def _svg_export(self, filepath):
        """Export to svg file filepath"""

        with self.print_zoom():
            grid = self.main_window.grid

            generator = QSvgGenerator()
            generator.setFileName(str(filepath))

            # Get area for svg export
            svg_area = SvgExportAreaDialog(self.main_window, grid).area
            if svg_area is None:
                return

            rows = self.get_paint_rows(svg_area)
            columns = self.get_paint_columns(svg_area)
            total_height = self.get_total_height(svg_area)
            total_width = self.get_total_width(svg_area)

            generator.setSize(QSize(total_width, total_height))
            paint_rect = QRectF(0, 0, total_width, total_height)
            generator.setViewBox(paint_rect)
            option = QStyleOptionViewItem()

            painter = QPainter(generator)

            self.paint(painter, option, paint_rect, rows, columns)

            painter.end()

    @contextmanager
    def print_zoom(self, zoom=1.0):
        """Decorator for tasks that have to take place in standard zoom"""

        __zoom = self.main_window.grid.zoom
        self.main_window.grid.zoom = zoom
        yield
        self.main_window.grid.zoom = __zoom

    def get_paint_rows(self, area):
        """Iterator of rows to paint"""

        rows = self.main_window.grid.model.shape[0]
        top, _, bottom, _ = area
        top = max(0, min(rows - 1, top))
        bottom = max(0, min(rows - 1, bottom))
        if top == -1:
            top = 0
        if bottom == -1:
            bottom = self.main_window.grid.model.shape[0]

        return range(top, bottom + 1)

    def get_paint_columns(self, area):
        """Iterator of columns to paint"""

        columns = self.main_window.grid.model.shape[1]
        _, left, _, right = area
        left = max(0, min(columns - 1, left))
        right = max(0, min(columns - 1, right))
        if left == -1:
            left = 0
        if right == -1:
            right = self.main_window.grid.model.shape[1]

        return range(left, right + 1)

    def get_total_height(self, area):
        """Total height of paint_rows"""

        grid = self.main_window.grid
        return sum(grid.rowHeight(row) for row in self.get_paint_rows(area))

    def get_total_width(self, area):
        """Total height of paint_columns"""

        grid = self.main_window.grid
        return sum(grid.columnWidth(column)
                   for column in self.get_paint_columns(area))

    def paint(self, painter, option, paint_rect, rows, columns):
        """Grid paint workflow for printing and svg export"""

        grid = self.main_window.grid
        code_array = grid.model.code_array
        cell_attributes = code_array.cell_attributes

        x_offset = grid.columnViewportPosition(0)
        y_offset = grid.rowViewportPosition(0)

        max_width = 0
        max_height = 0

        for row in rows:
            for column in columns:
                key = row, column, grid.table
                merging_cell = cell_attributes.get_merging_cell(key)
                if merging_cell is None \
                   or merging_cell[0] == row and merging_cell[1] == column:

                    idx = grid.model.index(row, column)
                    visual_rect = grid.visualRect(idx)
                    x = max(0, visual_rect.x() - x_offset)
                    y = max(0, visual_rect.y() - y_offset)
                    width = visual_rect.width()
                    if visual_rect.x() - x_offset < 0:
                        width += visual_rect.x() - x_offset
                    height = visual_rect.height()
                    if visual_rect.y() - y_offset < 0:
                        height += visual_rect.y() - y_offset

                    option.rect = QRect(x, y, width, height)
                    option.rectf = QRectF(x, y, width, height)

                    max_width = max(max_width, x + width)
                    max_height = max(max_height, y + height)
                    # painter.setClipRect(option.rectf)

                    option.text = code_array(key)
                    option.widget = grid

                    grid.itemDelegate().paint(painter, option, idx)

        # Draw outer boundary rect
        painter.setPen(QPen(QBrush(Qt.gray), 2))
        painter.drawRect(paint_rect)

    @handle_changed_since_save
    def file_quit(self):
        """Program exit workflow"""

        self.main_window.settings.save()
        self.main_window.application.quit()

    # Edit menu

    def delete(self, description_tpl="Delete selection {}"):
        """Delete cells in selection"""

        grid = self.main_window.grid
        model = grid.model
        selection = grid.selection

        description = description_tpl.format(selection)

        for row, column in selection.cell_generator(model.shape):
            key = row, column, grid.table
            if not grid.model.code_array.cell_attributes[key]['locked']:
                # Pop item
                index = model.index(row, column, QModelIndex())
                command = commands.SetCellCode(None, model, index, description)
                self.main_window.undo_stack.push(command)

    def edit_cut(self):
        """Edit -> Cut workflow"""

        self.edit_copy()
        self.delete(description_tpl="Cut selection {}")

    def edit_copy(self):
        """Edit -> Copy workflow

        Copies selected grid code to clipboard

        """

        grid = self.main_window.grid
        table = grid.table
        selection = grid.selection
        bbox = selection.get_grid_bbox(grid.model.shape)
        (top, left), (bottom, right) = bbox

        data = []

        for row in range(top, bottom + 1):
            data.append([])
            for column in range(left, right + 1):
                if (row, column) in selection:
                    code = grid.model.code_array((row, column, table))
                    if code is None:
                        code = ""
                    code = code.replace("\n", "\u000C")  # Replace LF by FF
                else:
                    code = ""
                data[-1].append(code)

        data_string = "\n".join("\t".join(line) for line in data)

        clipboard = QApplication.clipboard()
        clipboard.setText(data_string)

    def _copy_results_current(self, grid):
        """Copy cell results for the current cell"""

        current = grid.current
        data = grid.model.code_array[current]
        if data is None:
            return

        clipboard = QApplication.clipboard()

        # Get renderer for current cell
        renderer = grid.model.code_array.cell_attributes[current]["renderer"]

        if renderer == "text":
            clipboard.setText(repr(data))

        elif renderer == "image":
            if isinstance(data, QImage):
                clipboard.setImage(data)
            else:
                # We may have an svg image here
                try:
                    svg_bytes = bytes(data)
                except TypeError:
                    svg_bytes = bytes(data, encoding='utf-8')
                if is_svg(svg_bytes):
                    mime_data = QMimeData()
                    mime_data.setData("image/svg+xml", svg_bytes)
                    clipboard.setMimeData(mime_data)

        elif renderer == "markup":
            mime_data = QMimeData()
            mime_data.setHtml(str(data))

            # Also copy data as plain text
            doc = QTextDocument()
            doc.setHtml(str(data))
            mime_data.setText(doc.toPlainText())

            clipboard.setMimeData(mime_data)

        elif renderer == "matplotlib" and isinstance(data,
                                                     matplotlib_figure.Figure):
            # We copy and svg to the clipboard
            svg_filelike = io.BytesIO()
            png_filelike = io.BytesIO()
            data.savefig(svg_filelike, format="svg")
            data.savefig(png_filelike, format="png")
            svg_bytes = (svg_filelike.getvalue())
            png_image = QImage().fromData(png_filelike.getvalue())
            mime_data = QMimeData()
            mime_data.setData("image/svg+xml", svg_bytes)
            mime_data.setImageData(png_image)
            clipboard.setMimeData(mime_data)

    def _copy_results_selection(self, grid):
        """Copy repr of selected cells result objects to the clipboard"""

        def repr_nn(ele):
            """repr which returns '' if ele is None"""

            if ele is None:
                return ''
            return repr(ele)

        table = grid.table
        selection = grid.selection
        bbox = selection.get_grid_bbox(grid.model.shape)
        (top, left), (bottom, right) = bbox

        data = grid.model.code_array[top:bottom+1, left:right+1, table]
        data_string = "\n".join("\t".join(map(repr_nn, line)) for line in data)

        clipboard = QApplication.clipboard()
        clipboard.setText(data_string)

    def edit_copy_results(self):
        """Edit -> Copy results workflow

        If a selection is present then repr of selected grid cells result
        objects are copied to the clipboard.

        If no selection is present, the current cell results are copied to the
        clipboard. This can be plain text, html, a png image or an svg image.

        """

        grid = self.main_window.grid

        if grid.has_selection():
            self._copy_results_selection(grid)
        else:
            self._copy_results_current(grid)

    def _paste_to_selection(self, selection, data):
        """Pastes data into grid filling the selection"""

        grid = self.main_window.grid
        model = grid.model
        (top, left), (bottom, right) = selection.get_grid_bbox(model.shape)
        table = grid.table
        code_array = grid.model.code_array
        undo_stack = self.main_window.undo_stack

        description_tpl = "Paste clipboard to {}"
        description = description_tpl.format(selection)

        command = None

        paste_gen = (line.split("\t") for line in data.split("\n"))
        for row, line in enumerate(cycle(paste_gen)):
            paste_row = row + top
            if paste_row > bottom or (paste_row, 0, table) not in code_array:
                break
            for column, value in enumerate(cycle(line)):
                paste_column = column + left
                if ((paste_row, paste_column, table) in code_array
                        and paste_column <= right):
                    if (paste_row, paste_column) in selection:
                        index = model.index(paste_row, paste_column,
                                            QModelIndex())
                        # Preserve line breaks
                        value = value.replace("\u000C", "\n")
                        cmd = commands.SetCellCode(value, model, index,
                                                   description)
                        if command is None:
                            command = cmd
                        else:
                            command.mergeWith(cmd)
                else:
                    break
        undo_stack.push(command)

    def _paste_to_current(self, data):
        """Pastes data into grid starting from the current cell"""

        grid = self.main_window.grid
        model = grid.model
        top, left, table = current = grid.current
        code_array = grid.model.code_array
        undo_stack = self.main_window.undo_stack

        description_tpl = "Paste clipboard starting from cell {}"
        description = description_tpl.format(current)

        command = None

        paste_gen = (line.split("\t") for line in data.split("\n"))
        for row, line in enumerate(paste_gen):
            paste_row = row + top
            if (paste_row, 0, table) not in code_array:
                break
            for column, value in enumerate(line):
                paste_column = column + left
                if (paste_row, paste_column, table) in code_array:
                    index = model.index(paste_row, paste_column, QModelIndex())
                    # Preserve line breaks
                    value = value.replace("\u000C", "\n")
                    cmd = commands.SetCellCode(value, model, index,
                                               description)
                    if command is None:
                        command = cmd
                    else:
                        command.mergeWith(cmd)
                else:
                    break
        undo_stack.push(command)

    def edit_paste(self):
        """Edit -> Paste workflow

        Pastes text clipboard data

        If no selection is present, data is pasted starting with the current
        cell. If a selection is present, data is pasted fully if the selection
        is smaller. If the selection is larger then data is duplicated.

        """

        grid = self.main_window.grid

        clipboard = QApplication.clipboard()
        data = clipboard.text()

        if data:
            # Change the main window filepath state
            self.main_window.settings.changed_since_save = True

            with self.busy_cursor():
                if grid.has_selection():
                    self._paste_to_selection(grid.selection, data)
                else:
                    self._paste_to_current(data)

    def _paste_svg(self, svg, index):
        """Pastes svg image into cell

        Parameters
        ----------
         * svg: string
        \tSVG data
         * index: QModelIndex
        \tTarget cell index

        """

        codelines = svg.splitlines()
        codelines[0] = '"""' + codelines[0]
        codelines[-1] = codelines[-1] + '"""'
        code = "\n".join(codelines)

        model = self.main_window.grid.model
        description = "Insert svg image into cell {}".format(index)

        self.main_window.grid.on_image_renderer_pressed(True)
        with self.disable_entryline_updates():
            command = commands.SetCellCode(code, model, index, description)
            self.main_window.undo_stack.push(command)

    def _paste_image(self, image_data, index):
        """Pastes svg image into cell

        Parameters
        ----------
         * image_data: bytes
        \tRaw image data. May be anything that QImage handles.
         * index: QModelIndex
        \tTarget cell index

        """

        def gen_chunk(string, length):
            for i in range(0, len(string), length):
                yield string[i:i+length]

        repr_image_data = repr(b85encode(bz2.compress(image_data)))
        newline = "'\n+b'"

        image_data_str = newline.join(gen_chunk(repr_image_data, 8000))

        code_lines = [
            "data = bz2.decompress(base64.b85decode(",
            image_data_str,
            "))",
            "qimg = QImage()",
            "QImage.loadFromData(qimg, data)",
            "qimg",
        ]

        code = "\n".join(code_lines)

        model = self.main_window.grid.model
        description = "Insert image into cell {}".format(index)

        self.main_window.grid.on_image_renderer_pressed(True)
        with self.disable_entryline_updates():
            command = commands.SetCellCode(code, model, index, description)
            self.main_window.undo_stack.push(command)

    def edit_paste_as(self):
        """Pastes clipboard into one cell using a user specified mime type"""

        grid = self.main_window.grid
        model = grid.model

        # The mimetypes that are supported by pyspread
        mimetypes = ("image", "text/html", "text/plain")
        clipboard = QApplication.clipboard()
        formats = clipboard.mimeData().formats()

        items = [fmt for fmt in formats if any(m in fmt for m in mimetypes)]
        if not items:
            return
        elif len(items) == 1:
            item = items[0]
        else:
            item, ok = QInputDialog.getItem(self.main_window, "Paste as",
                                            "Choose mime type", items,
                                            current=0, editable=False)
            if not ok:
                return

        row, column, table = current = grid.current  # Target cell key

        description_tpl = "Paste {} from clipboard into cell {}"
        description = description_tpl.format(item, current)

        index = model.index(row, column, QModelIndex())

        mime_data = clipboard.mimeData()

        if item == "image/svg+xml":
            # SVG Image
            if mime_data:
                svg = mime_data.data("image/svg+xml")
                self._paste_svg(str(svg, encoding='utf-8'), index)

        elif "image" in item and mime_data.hasImage():
            # Bitmap Image
            image = clipboard.image()
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            image.save(buffer, "PNG")
            buffer.seek(0)
            image_data = buffer.readAll()
            buffer.close()
            self._paste_image(image_data, index)

        elif item == "text/html" and mime_data.hasHtml():
            # HTML content
            html = mime_data.html()
            command = commands.SetCellCode(html, model, index, description)
            self.main_window.undo_stack.push(command)
            grid.on_markup_renderer_pressed(True)

        elif item == "text/plain":
            # Normal code
            code = clipboard.text()
            if code:
                command = commands.SetCellCode(code, model, index, description)
                self.main_window.undo_stack.push(command)

        else:
            # Unknown mime type
            return NotImplemented

    def edit_find(self):
        """Edit -> Find workflow, opens FindDialog"""

        find_dialog = FindDialog(self.main_window)
        find_dialog.show()
        find_dialog.raise_()
        find_dialog.activateWindow()

    def _get_next_match(self, find_dialog):
        """Returns tuple of find string and next matching cell key"""

        grid = self.main_window.grid
        findnextmatch = grid.model.code_array.findnextmatch

        find_editor = find_dialog.search_text_editor
        find_string = find_editor.text()

        if find_dialog.from_start_checkbox.isChecked():
            start_key = 0, 0, grid.table
        elif find_dialog.backward_checkbox.isChecked():
            start_key = grid.row - 1, grid.column, grid.table
        else:
            start_key = grid.row + 1, grid.column, grid.table

        return find_string, findnextmatch(
                start_key, find_string,
                up=find_dialog.backward_checkbox.isChecked(),
                word=find_dialog.word_checkbox.isChecked(),
                case=find_dialog.case_checkbox.isChecked(),
                regexp=find_dialog.regex_checkbox.isChecked(),
                results=find_dialog.results_checkbox.isChecked())

    def _display_match_msg(self, find_string, next_match, regexp):
        """Displays find match message in statusbar"""

        str_name = "Regular expression" if regexp else "String"
        msg_tpl = "{str_name} {find_string} found in cell {next_match}."
        msg = msg_tpl.format(str_name=str_name,
                             find_string=find_string,
                             next_match=next_match)
        self.main_window.statusBar().showMessage(msg)

    def find_dialog_on_find(self, find_dialog):
        """Edit -> Find workflow, after pressing find button in FindDialog"""

        find_string, next_match = self._get_next_match(find_dialog)

        if next_match:
            self.main_window.grid.current = next_match

            regexp = find_dialog.regex_checkbox.isChecked()
            self._display_match_msg(find_string, next_match, regexp)

            if find_dialog.from_start_checkbox.isChecked():
                find_dialog.from_start_checkbox.setChecked(False)

    def edit_find_next(self):
        """Edit -> Find next workflow"""

        grid = self.main_window.grid
        findnextmatch = grid.model.code_array.findnextmatch

        find_editor = self.main_window.find_toolbar.find_editor
        find_string = find_editor.text()

        if find_editor.up:
            start_key = grid.row - 1, grid.column, grid.table
        else:
            start_key = grid.row + 1, grid.column, grid.table

        next_match = findnextmatch(start_key, find_string,
                                   up=find_editor.up,
                                   word=find_editor.word,
                                   case=find_editor.case,
                                   regexp=find_editor.regexp,
                                   results=find_editor.results)
        if next_match:
            grid.current = next_match

            self._display_match_msg(find_string, next_match,
                                    find_editor.regexp)

    def edit_replace(self):
        """Edit -> Replace workflow, opens ReplaceDialog"""

        find_dialog = ReplaceDialog(self.main_window)
        find_dialog.show()
        find_dialog.raise_()
        find_dialog.activateWindow()

    def replace_dialog_on_replace(self, replace_dialog, toggled=False, max_=1):
        """Edit -> Replace workflow when pushing Replace in ReplaceDialog

        Returns True if there is a match

        """

        model = self.main_window.grid.model

        find_string, next_match = self._get_next_match(replace_dialog)
        replace_string = replace_dialog.replace_text_editor.text()

        if next_match:
            old_code = model.code_array(next_match)
            new_code = old_code.replace(find_string, replace_string, max_)

            description_tpl = "Replaced {old} with {new} in cell {key}."
            description = description_tpl.format(old=old_code, new=new_code,
                                                 key=next_match)
            index = model.index(*next_match[:2])
            command = commands.SetCellCode(new_code, model, index, description)
            self.main_window.undo_stack.push(command)

            self.main_window.grid.current = next_match

            self.main_window.statusBar().showMessage(description)

            if replace_dialog.from_start_checkbox.isChecked():
                replace_dialog.from_start_checkbox.setChecked(False)

            return True

    def replace_dialog_on_replace_all(self, replace_dialog):
        """Edit -> Replace workflow when pushing ReplaceAll in ReplaceDialog"""

        while self.replace_dialog_on_replace(replace_dialog, max_=-1):
            pass

    def edit_resize(self):
        """Edit -> Resize workflow"""

        grid = self.main_window.grid

        maxshape = self.main_window.settings.maxshape

        # Get grid shape from user
        old_shape = grid.model.code_array.shape
        title = "Resize grid"
        shape = GridShapeDialog(self.main_window, old_shape, title=title).shape
        if shape is None:
            # Abort changes because the dialog has been canceled
            return
        elif any(ax == 0 for ax in shape):
            msg = "Invalid grid shape {}.".format(shape)
            self.main_window.statusBar().showMessage(msg)
            return
        elif any(ax > axmax for axmax, ax in zip(maxshape, shape)):
            msg = "Grid shape {} exceeds {}.".format(shape, maxshape)
            self.main_window.statusBar().showMessage(msg)
            return

        self.main_window.grid.current = 0, 0, 0

        description = "Resize grid to {}".format(shape)

        with self.disable_entryline_updates():
            command = commands.SetGridSize(grid, old_shape, shape, description)
            self.main_window.undo_stack.push(command)

        # Select upper left cell because initial selection behaves strangely
        self.main_window.grid.reset_selection()

    # View menu

    def view_goto_cell(self):
        """View -> Go to cell workflow"""

        # Get cell key from user
        shape = self.main_window.grid.model.shape
        key = CellKeyDialog(self.main_window, shape).key

        if key is not None:
            self.main_window.grid.current = key

    # Format menu

    def format_copy_format(self):
        """Copies the format of the selected cells to the Clipboard

        Cells are shifted so that the top left bbox corner is at 0,0

        """

        def remove_tabu_keys(attr):
            """Remove keys that are not copied from attr"""

            tabu_attrs = "merge_area", "frozen"
            for tabu_attr in tabu_attrs:
                try:
                    attrs.pop(tabu_attr)
                except KeyError:
                    pass

        grid = self.main_window.grid
        code_array = grid.model.code_array
        cell_attributes = code_array.cell_attributes

        row, column, table = grid.current

        # Cell attributes

        new_cell_attributes = []
        selection = grid.selection

        # Format content is shifted so that the top left corner is 0,0
        (top, left), (bottom, right) = \
            selection.get_grid_bbox(grid.model.shape)

        table_cell_attributes = deepcopy(cell_attributes.for_table(table))
        for __selection, _, attrs in table_cell_attributes:
            new_selection = selection & __selection
            if new_selection:
                # We do not copy merged cells and cell renderers
                remove_tabu_keys(attrs)
                new_shifted_selection = new_selection.shifted(-top, -left)
                cell_attribute = new_shifted_selection.parameters, attrs
                new_cell_attributes.append(cell_attribute)

        ca_repr = bytes(repr(new_cell_attributes), encoding='utf-8')

        clipboard = QApplication.clipboard()
        mime_data = QMimeData()
        mime_data.setData("application/x-pyspread-cell-attributes", ca_repr)
        clipboard.setMimeData(mime_data)

    def format_paste_format(self):
        """Pastes cell formats

        Pasting starts at cursor or at top left bbox corner

        """

        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        grid = self.main_window.grid
        model = grid.model

        row, column, table = grid.current

        if "application/x-pyspread-cell-attributes" not in mime_data.formats():
            return

        cas_data = mime_data.data("application/x-pyspread-cell-attributes")
        cas_data_str = str(cas_data, encoding='utf-8')
        cas = literal_eval(cas_data_str)
        assert isinstance(cas, list)

        tabu_attrs = "merge_area", "frozen"

        description_tpl = "Paste format for selections {}"
        description = description_tpl.format([ca[0] for ca in cas])

        for selection_params, attrs in cas:
            if not any(tabu_attr in attrs for tabu_attr in tabu_attrs):
                selection = Selection(*selection_params)
                shifted_selection = selection.shifted(row, column)
                new_cell_attribute = shifted_selection, table, attrs

                selected_idx = []
                for key in shifted_selection.cell_generator(model.shape):
                    selected_idx.append(model.index(*key))

                command = commands.SetCellFormat(new_cell_attribute, model,
                                                 grid.currentIndex(),
                                                 selected_idx, description)
                self.main_window.undo_stack.push(command)

    # Macro menu

    def macro_insert_image(self):
        """Insert image workflow"""

        dial = ImageFileOpenDialog(self.main_window)
        if not dial.file_path:
            return  # Cancel pressed

        filepath = Path(dial.file_path)

        index = self.main_window.grid.currentIndex()

        if filepath.suffix == ".svg":
            try:
                with open(filepath, "r") as svgfile:
                    svg = svgfile.read()
            except OSError as err:
                msg_tpl = "Error opening file {filepath}: {err}."
                msg = msg_tpl.format(filepath=filepath, err=err)
                self.main_window.statusBar().showMessage(msg)
                return
            self._paste_svg(svg, index)
        else:
            try:
                with open(filepath, "rb") as imgfile:
                    image_data = imgfile.read()
            except OSError as err:
                msg_tpl = "Error opening file {filepath}: {err}."
                msg = msg_tpl.format(filepath=filepath, err=err)
                self.main_window.statusBar().showMessage(msg)
                return
            self._paste_image(image_data, index)

    def macro_insert_chart(self):
        """Insert chart workflow"""

        code_array = self.main_window.grid.model.code_array
        code = code_array(self.main_window.grid.current)

        chart_dialog = ChartDialog(self.main_window)
        if code is not None:
            chart_dialog.editor.setPlainText(code)
        chart_dialog.show()
        if chart_dialog.exec_() == ChartDialog.Accepted:
            code = chart_dialog.editor.toPlainText()
            index = self.main_window.grid.currentIndex()
            self.main_window.grid.on_matplotlib_renderer_pressed(True)

            model = self.main_window.grid.model
            description = "Insert chart into cell {}".format(index)
            command = commands.SetCellCode(code, model, index, description)
            self.main_window.undo_stack.push(command)
