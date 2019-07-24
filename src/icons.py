#!/usr/bin/env python3
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

import os
from pathlib import PurePath
from PyQt5.QtGui import QIcon

PYSPREAD_PATH = \
    PurePath(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
ICON_PATH = PYSPREAD_PATH / 'share/icons'
ACTION_PATH = ICON_PATH / 'actions'
STATUS_PATH = ICON_PATH / 'status'
CHARTS_PATH = ICON_PATH / 'charts'
#MPL_TEMPLATE_PATH = PYSPREAD_PATH / 'share/templates/matplotlib'


class Icon(QIcon):
    """Class for getting items from names"""

    icon_path = {
        "pyspread": str(ICON_PATH / 'pyspread.svg'),

        # Status icons
        "warning": str(STATUS_PATH / 'dialog-warning.svg'),

        # File menu icons
        "new": str(ACTION_PATH / 'document-new.svg'),
        "open": str(ACTION_PATH / 'document-open.svg'),
        "save": str(ACTION_PATH / 'document-save.svg'),
        "save_as": str(ACTION_PATH / 'document-save-as.svg'),
        "import": str(ACTION_PATH / 'document-import.svg'),
        "export": str(ACTION_PATH / 'document-export.svg'),
        "approve": str(ACTION_PATH / 'document-approve.svg'),
        "clear_globals": str(ACTION_PATH / 'edit-clear.svg'),
        "page_setup": str(ACTION_PATH / 'document-page-setup.svg'),
        "print_preview": str(ACTION_PATH / 'document-print-preview.svg'),
        "print": str(ACTION_PATH / 'document-print.svg'),
        "preferences": str(ACTION_PATH / 'document-properties.svg'),
        "new_gpg_key": str(ACTION_PATH / 'document-new-gpg-key.svg'),
        "quit": str(ACTION_PATH / 'document-log-out.svg'),

        # Edit menu icons
        "undo": str(ACTION_PATH / 'edit-undo.svg'),
        "redo": str(ACTION_PATH / 'edit-redo.svg'),
        "cut": str(ACTION_PATH / 'edit-cut.svg'),
        "copy": str(ACTION_PATH / 'edit-copy.svg'),
        "copy_results": str(ACTION_PATH / 'edit-copy-results.svg'),
        "paste": str(ACTION_PATH / 'edit-paste.svg'),
        "paste_as": str(ACTION_PATH / 'edit-paste-as.svg'),
        "select_all": str(ACTION_PATH / 'edit-select-all.svg'),
        "find": str(ACTION_PATH / 'edit-find.svg'),
        "replace": str(ACTION_PATH / 'edit-find-replace.svg'),
        "quote": str(ACTION_PATH / 'edit-quote.svg'),
        "sort_ascending": str(ACTION_PATH / 'edit-sort-ascending.svg'),
        "sort_descending": str(ACTION_PATH / 'edit-sort-descending.svg'),
        "insert_row": str(ACTION_PATH / 'edit-insert-row.svg'),
        "insert_column": str(ACTION_PATH / 'edit-insert-column.svg'),
        "insert_table": str(ACTION_PATH / 'edit-insert-table.svg'),
        "delete_row": str(ACTION_PATH / 'edit-delete-row.svg'),
        "delete_column": str(ACTION_PATH / 'edit-delete-column.svg'),
        "delete_table": str(ACTION_PATH / 'edit-delete-table.svg'),
        "resize_grid": str(ACTION_PATH / 'edit-resize-grid.svg'),

        # View menu icons
        "fullscreen": str(ACTION_PATH / 'view-fullscreen.svg'),
        "goto_cell": str(ACTION_PATH / 'view-goto-cell.svg'),
        "check_spelling": str(ACTION_PATH / 'view-check-spelling.svg'),
        "zoom_in": str(ACTION_PATH / 'view-zoom-in.svg'),
        "zoom_out": str(ACTION_PATH / 'view-zoom-out.svg'),
        "zoom_1": str(ACTION_PATH / 'view-zoom-original.svg'),
        "zoom_fit": str(ACTION_PATH / 'view-zoom-fit-best.svg'),
        "refresh": str(ACTION_PATH / 'view-refresh.svg'),
        "toggle_periodic_updates": str(ACTION_PATH / 'view-timer.svg'),
        "show_frozen": str(ACTION_PATH / 'view-show-frozen.svg'),

        # Format menu icons
        "copy_format": str(ACTION_PATH / 'format-copy.svg'),
        "paste_format": str(ACTION_PATH / 'format-paste.svg'),
        "font_dialog": str(ACTION_PATH / 'format-font.svg'),
        "bold": str(ACTION_PATH / 'format-text-bold.svg'),
        "italics": str(ACTION_PATH / 'format-text-italic.svg'),
        "underline": str(ACTION_PATH / 'format-text-underline.svg'),
        "strikethrough": str(ACTION_PATH / 'format-text-strikethrough.svg'),
        "markup": str(ACTION_PATH / 'format-cell-markup.svg'),
        "image": str(ACTION_PATH / 'format-cell-image.svg'),
        "text": str(ACTION_PATH / 'format-cell-text.svg'),
        "matplotlib": str(ACTION_PATH / 'format-cell-chart.svg'),
        "line_color": str(ACTION_PATH / 'format-line-color.svg'),
        "text_color": str(ACTION_PATH / 'format-text-color.svg'),
        "background_color": str(ACTION_PATH / 'format-background-color.svg'),
        "rotate_0": str(ACTION_PATH / 'format-cell-rotate-0.svg'),
        "rotate_90": str(ACTION_PATH / 'format-cell-rotate-90.svg'),
        "rotate_180": str(ACTION_PATH / 'format-cell-rotate-180.svg'),
        "rotate_270": str(ACTION_PATH / 'format-cell-rotate-270.svg'),
        "justify_left": str(ACTION_PATH / 'format-justify-left.svg'),
        "justify_fill": str(ACTION_PATH / 'format-justify-fill.svg'),
        "justify_center": str(ACTION_PATH / 'format-justify-center.svg'),
        "justify_right": str(ACTION_PATH / 'format-justify-right.svg'),
        "align_top": str(ACTION_PATH / 'format-text-align-top.svg'),
        "align_center": str(ACTION_PATH / 'format-text-align-center.svg'),
        "align_bottom": str(ACTION_PATH / 'format-text-align-bottom.svg'),
        "border_menu": str(ACTION_PATH / 'format-borders-all.svg'),
        "format_borders_all": str(ACTION_PATH / 'format-borders-all.svg'),
        "format_borders_top": str(ACTION_PATH / 'format-borders-top.svg'),
        "format_borders_bottom": str(ACTION_PATH
                                     / 'format-borders-bottom.svg'),
        "format_borders_left": str(ACTION_PATH / 'format-borders-left.svg'),
        "format_borders_right": str(ACTION_PATH / 'format-borders-right.svg'),
        "format_borders_outer": str(ACTION_PATH / 'format-borders-outer.svg'),
        "format_borders_inner": str(ACTION_PATH / 'format-borders-inner.svg'),
        "format_borders_top_bottom": str(ACTION_PATH
                                         / 'format-borders-top-bottom.svg'),
        "format_borders": str(ACTION_PATH / 'format-borders-4.svg'),
        "format_borders_0": str(ACTION_PATH / 'format-borders-0.svg'),
        "format_borders_1": str(ACTION_PATH / 'format-borders-1.svg'),
        "format_borders_2": str(ACTION_PATH / 'format-borders-2.svg'),
        "format_borders_4": str(ACTION_PATH / 'format-borders-4.svg'),
        "format_borders_8": str(ACTION_PATH / 'format-borders-8.svg'),
        "format_borders_16": str(ACTION_PATH / 'format-borders-16.svg'),
        "format_borders_32": str(ACTION_PATH / 'format-borders-32.svg'),
        "format_borders_64": str(ACTION_PATH / 'format-borders-64.svg'),

        "freeze": str(ACTION_PATH / 'format-freeze.svg'),
        "lock": str(ACTION_PATH / 'format-lock.svg'),
        "merge_cells": str(ACTION_PATH / 'format-merge-cells.svg'),

        # Macro menu icons
        "insert_image": str(ACTION_PATH / 'macro-insert-image.svg'),
        "link_image": str(ACTION_PATH / 'macro-link-image.svg'),
        "insert_chart": str(ACTION_PATH / 'macro-insert-chart.svg'),

        # Help menu icons
        "help": str(ACTION_PATH / 'help-browser.svg'),
        "tutorial": str(ACTION_PATH / 'help-tutorial.svg'),
        "faq": str(ACTION_PATH / 'help-faq.svg'),
        "dependencies": str(ACTION_PATH / 'help-dependencies.svg'),

        # Chart dialog template icons
        "chart_pie_1_1": str(CHARTS_PATH / 'chart_pie_1_1.svg'),
        "chart_line_1_1": str(CHARTS_PATH / 'chart_line_1_1.svg'),
        "chart_area_1_1": str(CHARTS_PATH / 'chart_area_1_1.svg'),
        "chart_column_1_1": str(CHARTS_PATH / 'chart_column_1_1.svg'),
        "chart_column_1_2": str(CHARTS_PATH / 'chart_column_1_2.svg'),
        "chart_boxplot_2_2": str(CHARTS_PATH / 'chart_boxplot_2_2.svg'),
        "chart_histogram_1_1": str(CHARTS_PATH / 'chart_histogram_1_1.svg'),
        "chart_scatterhist_1_1": str(CHARTS_PATH/'chart_scatterhist_1_1.svg'),
        "chart_matrix_1_1": str(CHARTS_PATH / 'chart_matrix_1_1.svg'),
        "chart_surface_2_1": str(CHARTS_PATH / 'chart_surface_2_1.svg'),

    }

    def __init__(self, name):
        super().__init__(self.icon_path[name])
