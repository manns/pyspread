#!/usr/bin/python3
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

workflows
---------

Workflows for pyspread

"""

from base64 import b85encode
import bz2
from contextlib import contextmanager
from itertools import cycle
import io
import os.path
from pathlib import Path
from shutil import move
import sys
from tempfile import NamedTemporaryFile

from PyQt5.QtCore import Qt, QMimeData, QModelIndex, QBuffer
from PyQt5.QtGui import QImage as BasicQImage
from PyQt5.QtGui import QTextDocument, QImage
from PyQt5.QtWidgets import QApplication, QProgressDialog, QMessageBox
from PyQt5.QtWidgets import QInputDialog

try:
    import matplotlib.figure as matplotlib_figure
except ImportError:
    matplotlib_figure = None

from src.commands import CommandSetCellCode
from src.dialogs import DiscardChangesDialog, FileOpenDialog, GridShapeDialog
from src.dialogs import FileSaveDialog, ImageFileOpenDialog, ChartDialog
from src.dialogs import CellKeyDialog
from src.interfaces.pys import PysReader, PysWriter
from src.lib.hashing import sign, verify
from src.lib.typechecks import is_svg


class Workflows:
    def __init__(self, main_window):
        self.main_window = main_window

    @contextmanager
    def progress_dialog(self, title, label, maximum, min_duration=3000):
        """Context manager that displays a file progress dialog"""

        progress_dialog = QProgressDialog(self.main_window)
        progress_dialog.setWindowTitle(title)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setLabelText(label)
        progress_dialog.setMaximum(maximum)
        progress_dialog.setMinimumDuration(min_duration)
        progress_dialog.show()
        progress_dialog.setValue(0)

        yield progress_dialog

        progress_dialog.setValue(maximum)

    @contextmanager
    def disable_entryline_updates(self):
        """Context manager for temporarily disabling the entry line"""

        self.main_window.entry_line.setUpdatesEnabled(False)
        yield
        self.main_window.entry_line.setUpdatesEnabled(True)

    def handle_changed_since_save(func):
        """Decorator to handle changes since last saving the document

        If changes are present then a dialog is displayed that asks if the
        changes shall be discarded.
        If the user selects Cancel then func is not executed.
        If the user selects Save then the file is saved and func is executed.
        If the user selects Discard then the file is not saved and func is
        executed.
        If no changes are present then func is directly executed.
        After executing func, reset_changed_since_save is called.

        """

        def function_wrapper(self):
            """Check changes and display and handle the dialog"""

            if self.main_window.settings.changed_since_save:
                choice = DiscardChangesDialog(self.main_window).choice
                if choice is None:
                    return
                elif not choice:
                    self.file_save()
            func(self)
            self.reset_changed_since_save()

        return function_wrapper

    def reset_changed_since_save(self):
        """Sets changed_since_save to False and updates the window title"""

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

        # Get the current filepath
        filepath = self.main_window.settings.last_file_input_path

        # Change the main window title
        window_title = "{filename} - pyspread".format(filename=filepath.name)
        self.main_window.setWindowTitle(window_title)

    @handle_changed_since_save
    def file_new(self):
        """File new workflow"""

        # Get grid shape from user
        old_shape = self.main_window.grid.model.code_array.shape
        shape = GridShapeDialog(self.main_window, old_shape).shape
        if shape is None:
            # Abort changes because the dialog has been canceled
            return

        # Reset grid
        self.main_window.grid.model.reset()

        # Set new shape
        self.main_window.grid.model.shape = shape

        # Select upper left cell because initial selection behaves strange
        self.main_window.grid.reset_selection()

        # Exit safe mode
        self.main_window.safe_mode = False

    @handle_changed_since_save
    def file_open(self):
        """File open workflow"""

        #TODO: Fix signature key issue
        code_array = self.main_window.grid.model.code_array

        # Get filepath from user
        file_open_dialog = FileOpenDialog(self.main_window)
        filepath = file_open_dialog.filepath
        chosen_filter = file_open_dialog.chosen_filter
        if not filepath or not chosen_filter:
            return  # Cancel pressed
        else:
            filepath = Path(filepath)
        filesize = os.path.getsize(filepath)

        # Reset grid
        self.main_window.grid.model.reset()

        # Is the file signed properly?
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
        if chosen_filter == "Pyspread uncompressed (*.pysu)":
            fopen = open
        else:
            fopen = bz2.open

        # Process events before showing the modal progress dialog
        self.main_window.application.processEvents()

        # Load file into grid
        with fopen(filepath, "rb") as infile:
            with self.progress_dialog("File open progress",
                                      "Opening {}...".format(filepath.name),
                                      filesize) as progress_dialog:
                for line in PysReader(infile, code_array):
                    progress_dialog.setValue(infile.tell())
                    self.main_window.application.processEvents()
                    if progress_dialog.wasCanceled():
                        self.main_window.grid.model.reset()
                        self.main_window.safe_mode = False
                        break

        # Explicitly set the grid shape
        shape = self.main_window.grid.model.code_array.shape
        self.main_window.grid.model.shape = shape

        # Update the cell spans because this is unsupported by the model
        self.main_window.grid.update_cell_spans()

        # Select upper left cell because initial selection behaves strangely
        self.main_window.grid.reset_selection()

        # Change the main window last input directory state
        self.main_window.settings.last_file_input_path = filepath

        # Change the main window filepath state
        self.main_window.settings.changed_since_save = False

    def sign_file(self, filepath):
        """Signs filepath if pyspread is not in safe mode"""

        if self.main_window.grid.model.code_array.safe_mode:
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
        with open(signature_path, 'wb') as signfile:
            signfile.write(signature)

        msg = "File saved and signed."
        self.main_window.statusBar().showMessage(msg)

    def _save(self, filepath):
        """Save filepath using chosen_filter

        Compresses save file if filepath.suffix == '.pys'

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
            except (IOError, ValueError) as err:
                tempfile.delete = True
                QMessageBox.critical(self.main_window, "Error saving file",
                                     str(err))
                return
        try:
            move(filename, filepath)

        except OSError as err:
            # No tmp file present
            QMessageBox.critical(self.main_window, "Error saving file", err)
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
        else:
            # New, changed file that has never been saved before
            self.file_save_as()

    def file_save_as(self):
        """File save as workflow"""

        # Get filepath from user
        file_save_dialog = FileSaveDialog(self.main_window)
        filepath = file_save_dialog.filepath
        if not filepath:
            return  # Cancel pressed
        else:
            filepath = Path(filepath)
        chosen_filter = file_save_dialog.chosen_filter
        filter_suffix = chosen_filter[-5:-1]  # e.g. '.pys'

        # Extend filepath suffix if needed
        if filepath.suffix != filter_suffix:
            filepath = filepath.with_suffix(filepath.suffix + filter_suffix)

        self._save(filepath)

    @handle_changed_since_save
    def file_quit(self):
        """Program exit workflow"""

        sys.exit()

    # Edit menu

    def copy(self):
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
            if isinstance(data, BasicQImage):
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

    def copy_results(self):
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
                        command = CommandSetCellCode(value, model, index,
                                                     description)
                        undo_stack.push(command)
                else:
                    break

    def _paste_to_current(self, data):
        """Pastes data into grid starting from the current cell"""

        grid = self.main_window.grid
        model = grid.model
        top, left, table = current = grid.current
        code_array = grid.model.code_array
        undo_stack = self.main_window.undo_stack

        description_tpl = "Paste clipboard starting from cell {}"
        description = description_tpl.format(current)

        paste_gen = (line.split("\t") for line in data.split("\n"))
        for row, line in enumerate(paste_gen):
            paste_row = row + top
            if (paste_row, 0, table) not in code_array:
                break
            for column, value in enumerate(line):
                paste_column = column + left
                if (paste_row, paste_column, table) in code_array:
                    index = model.index(paste_row, paste_column, QModelIndex())
                    command = CommandSetCellCode(value, model, index,
                                                 description)
                    undo_stack.push(command)
                else:
                    break

    def paste(self):
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
            command = CommandSetCellCode(code, model, index, description)
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

        code = (r'_load_img(base64.b85decode(' +
                repr(b85encode(image_data)) +
                '))'
                r' if exec("'
                r'def _load_img(data): qimg = QImage(); '
                r'QImage.loadFromData(qimg, data); '
                r'return qimg\n'
                r'") is None else None')

        model = self.main_window.grid.model
        description = "Insert image into cell {}".format(index)

        self.main_window.grid.on_image_renderer_pressed(True)
        with self.disable_entryline_updates():
            command = CommandSetCellCode(code, model, index, description)
            self.main_window.undo_stack.push(command)

    def paste_as(self):
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

        item, ok = QInputDialog.getItem(self.main_window, "Paste as",
                                        "Choose mime type", items, current=6,
                                        editable=False)
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
            command = CommandSetCellCode(html, model, index, description)
            self.main_window.undo_stack.push(command)
            grid.on_markup_renderer_pressed(True)

        elif item == "text/plain":
            # Normal code
            code = clipboard.text()
            if code:
                command = CommandSetCellCode(code, model, index, description)
                self.main_window.undo_stack.push(command)

        else:
            # Unknown mime type
            return NotImplemented

    # View menu

    def goto_cell(self):
        """View -> Go to cell workflow"""

        # Get cell key from user
        shape = self.main_window.grid.model.code_array.shape
        key = CellKeyDialog(self.main_window, shape).key

        if key is not None:
            self.main_window.grid.current = key

    # Macro menu

    def insert_image(self):
        """Insert image workflow"""

        image_file_open_dialog = ImageFileOpenDialog(self.main_window)
        filepath = image_file_open_dialog.filepath
        if not filepath:
            return  # Cancel pressed
        else:
            filepath = Path(filepath)
            chosen_filter = image_file_open_dialog.chosen_filter

        index = self.main_window.grid.currentIndex()

        if ".svg" in chosen_filter:
            with open(filepath, "r") as svgfile:
                svg = svgfile.read()
            self._paste_svg(svg, index)
        else:
            with open(filepath, "rb") as imgfile:
                image_data = imgfile.read()
            self._paste_image(image_data, index)

    def insert_chart(self):
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
            command = CommandSetCellCode(code, model, index, description)
            self.main_window.undo_stack.push(command)
