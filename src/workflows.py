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
import os.path
from pathlib import Path
from shutil import move
import sys
from tempfile import NamedTemporaryFile

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QProgressDialog, QMessageBox

from src.commands import CommandSetCellCode
from src.dialogs import DiscardChangesDialog, FileOpenDialog, GridShapeDialog
from src.dialogs import FileSaveDialog, ImageFileOpenDialog, ChartDialog
from src.dialogs import CellKeyDialog
from src.interfaces.pys import PysReader, PysWriter
from src.lib.hashing import sign, verify


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

    def _mime_preference(self):
        """Mime preferences  for pasting content

        Returns a preference list for clipboard mime data.
        Preference is assumed top to down.
        Generally speking:
        vector images > bitmap images > csv > text > html

        """

        mime_preferences = []

        # Vector images

        mime_preferences += [
            "image/svg+xml-compressed",
            "image/svg+xml",
        ]

        # Bitmap images

        mime_preferences += [
            "image/png",
            "image/tiff",
            "image/jpeg",
            "image/bmp",
        ]

        # Text

        mime_preferences += [
            "text/csv",
            "text/plain",
            "text/html",
        ]

        return mime_preferences

    def paste(self):
        """Edit -> Paste workflow

        Paste handles clipboard data by choosing amongst the available mime
        types. Paste As allows individual choice to both mime data choice and
        data post processing, e. g. how a table is distributed in the grid.


        TODO: Add puys and pysu to freedesktop.org shared mime data

        """

        clipboard = QApplication.clipboard()
        mimedata = clipboard.mimeData()
        print(mimedata.formats())

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

        if ".svg" in chosen_filter:
            with open(filepath, "r") as svgfile:
                codelines = svgfile.read().splitlines()
                codelines[0] = '"""' + codelines[0]
                codelines[-1] = codelines[-1] + '"""'
                code = "\n".join(codelines)
        else:
            with open(filepath, "rb") as imgfile:
                imgdata = b85encode(imgfile.read())

            code = (r'_load_img(base64.b85decode(' +
                    repr(imgdata) +
                    '))'
                    r' if exec("'
                    r'def _load_img(data): qimg = QImage(); '
                    r'QImage.loadFromData(qimg, data); '
                    r'return qimg\n'
                    r'") is None else None')

        index = self.main_window.grid.currentIndex()
        self.main_window.grid.on_image_renderer_pressed(True)
        self.main_window.entry_line.setUpdatesEnabled(False)

        model = self.main_window.grid.model
        description = "Insert image into cell {}".format(index)
        command = CommandSetCellCode(code, model, index, description)
        self.main_window.undo_stack.push(command)

        self.main_window.entry_line.setUpdatesEnabled(True)

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
