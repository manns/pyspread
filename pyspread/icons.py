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

* :class:`IconPath`
* :class:`IconConverter`
* :class:`Icon`

"""


from PyQt5.QtGui import QIcon

try:
    from pyspread.settings import (ICON_PATH, ACTION_PATH, STATUS_PATH,
                                   CHARTS_PATH)
except ImportError:
    from settings import ICON_PATH, ACTION_PATH, STATUS_PATH, CHARTS_PATH


class IconPath:
    """Holds icon paths as attributes"""

    pyspread = ICON_PATH / 'pyspread.svg'

    # Status icons
    safe_mode = STATUS_PATH / 'status-safe-mode.svg'
    selection_mode = STATUS_PATH / 'status-selection-mode.svg'

    # File menu icons
    new = ACTION_PATH / 'document-new.svg'
    open = ACTION_PATH / 'document-open.svg'
    save = ACTION_PATH / 'document-save.svg'
    save_as = ACTION_PATH / 'document-save-as.svg'
    imprt = ACTION_PATH / 'document-import.svg'
    export = ACTION_PATH / 'document-export.svg'
    approve = ACTION_PATH / 'document-approve.svg'
    clear_globals = ACTION_PATH / 'edit-clear.svg'
    page_setup = ACTION_PATH / 'document-page-setup.svg'
    print_preview = ACTION_PATH / 'document-print-preview.svg'
    print = ACTION_PATH / 'document-print.svg'
    preferences = ACTION_PATH / 'document-properties.svg'
    new_gpg_key = ACTION_PATH / 'document-new-gpg-key.svg'
    quit = ACTION_PATH / 'document-log-out.svg'

    # Edit menu icons
    undo = ACTION_PATH / 'edit-undo.svg'
    redo = ACTION_PATH / 'edit-redo.svg'
    cut = ACTION_PATH / 'edit-cut.svg'
    copy = ACTION_PATH / 'edit-copy.svg'
    copy_results = ACTION_PATH / 'edit-copy-results.svg'
    paste = ACTION_PATH / 'edit-paste.svg'
    paste_as = ACTION_PATH / 'edit-paste-as.svg'
    select_all = ACTION_PATH / 'edit-select-all.svg'
    find = ACTION_PATH / 'edit-find.svg'
    find_next = ACTION_PATH / 'edit-find-next.svg'
    replace = ACTION_PATH / 'edit-find-replace.svg'
    quote = ACTION_PATH / 'edit-quote.svg'
    sort_ascending = ACTION_PATH / 'edit-sort-ascending.svg'
    sort_descending = ACTION_PATH / 'edit-sort-descending.svg'
    insert_row = ACTION_PATH / 'edit-insert-row.svg'
    insert_column = ACTION_PATH / 'edit-insert-column.svg'
    insert_table = ACTION_PATH / 'edit-insert-table.svg'
    delete_row = ACTION_PATH / 'edit-delete-row.svg'
    delete_column = ACTION_PATH / 'edit-delete-column.svg'
    delete_table = ACTION_PATH / 'edit-delete-table.svg'
    resize_grid = ACTION_PATH / 'edit-resize-grid.svg'

    # View menu icons
    fullscreen = ACTION_PATH / 'view-fullscreen.svg'
    goto_cell = ACTION_PATH / 'view-goto-cell.svg'
    check_spelling = ACTION_PATH / 'view-check-spelling.svg'
    zoom_in = ACTION_PATH / 'view-zoom-in.svg'
    zoom_out = ACTION_PATH / 'view-zoom-out.svg'
    zoom_1 = ACTION_PATH / 'view-zoom-original.svg'
    refresh = ACTION_PATH / 'view-refresh.svg'
    toggle_periodic_updates = ACTION_PATH / 'view-timer.svg'
    show_frozen = ACTION_PATH / 'view-show-frozen.svg'

    # Format menu icons
    copy_format = ACTION_PATH / 'format-copy.svg'
    paste_format = ACTION_PATH / 'format-paste.svg'
    font_dialog = ACTION_PATH / 'format-font.svg'
    bold = ACTION_PATH / 'format-text-bold.svg'
    italics = ACTION_PATH / 'format-text-italic.svg'
    underline = ACTION_PATH / 'format-text-underline.svg'
    strikethrough = ACTION_PATH / 'format-text-strikethrough.svg'
    markup = ACTION_PATH / 'format-cell-markup.svg'
    image = ACTION_PATH / 'format-cell-image.svg'
    text = ACTION_PATH / 'format-cell-text.svg'
    matplotlib = ACTION_PATH / 'format-cell-chart.svg'
    line_color = ACTION_PATH / 'format-line-color.svg'
    text_color = ACTION_PATH / 'format-text-color.svg'
    background_color = ACTION_PATH / 'format-background-color.svg'
    rotate_0 = ACTION_PATH / 'format-cell-rotate-0.svg'
    rotate_90 = ACTION_PATH / 'format-cell-rotate-90.svg'
    rotate_180 = ACTION_PATH / 'format-cell-rotate-180.svg'
    rotate_270 = ACTION_PATH / 'format-cell-rotate-270.svg'
    justify_left = ACTION_PATH / 'format-justify-left.svg'
    justify_fill = ACTION_PATH / 'format-justify-fill.svg'
    justify_center = ACTION_PATH / 'format-justify-center.svg'
    justify_right = ACTION_PATH / 'format-justify-right.svg'
    align_top = ACTION_PATH / 'format-text-align-top.svg'
    align_center = ACTION_PATH / 'format-text-align-center.svg'
    align_bottom = ACTION_PATH / 'format-text-align-bottom.svg'
    border_menu = ACTION_PATH / 'format-borders-all.svg'
    format_borders_all = ACTION_PATH / 'format-borders-all.svg'
    format_borders_top = ACTION_PATH / 'format-borders-top.svg'
    format_borders_bottom = ACTION_PATH / 'format-borders-bottom.svg'
    format_borders_left = ACTION_PATH / 'format-borders-left.svg'
    format_borders_right = ACTION_PATH / 'format-borders-right.svg'
    format_borders_outer = ACTION_PATH / 'format-borders-outer.svg'
    format_borders_inner = ACTION_PATH / 'format-borders-inner.svg'
    format_borders_top_bottom = ACTION_PATH / 'format-borders-top-bottom.svg'
    format_borders = ACTION_PATH / 'format-borders-4.svg'
    format_borders_0 = ACTION_PATH / 'format-borders-0.svg'
    format_borders_1 = ACTION_PATH / 'format-borders-1.svg'
    format_borders_2 = ACTION_PATH / 'format-borders-2.svg'
    format_borders_4 = ACTION_PATH / 'format-borders-4.svg'
    format_borders_8 = ACTION_PATH / 'format-borders-8.svg'
    format_borders_16 = ACTION_PATH / 'format-borders-16.svg'
    format_borders_32 = ACTION_PATH / 'format-borders-32.svg'
    format_borders_64 = ACTION_PATH / 'format-borders-64.svg'

    freeze = ACTION_PATH / 'format-freeze.svg'
    lock = ACTION_PATH / 'format-lock.svg'
    button = ACTION_PATH / 'format-button.svg'
    merge_cells = ACTION_PATH / 'format-merge-cells.svg'

    # Macro menu icons
    insert_image = ACTION_PATH / 'macro-insert-image.svg'
    link_image = ACTION_PATH / 'macro-link-image.svg'
    insert_chart = ACTION_PATH / 'macro-insert-chart.svg'

    # Help menu icons
    help = ACTION_PATH / 'help-browser.svg'
    tutorial = ACTION_PATH / 'help-tutorial.svg'
    faq = ACTION_PATH / 'help-faq.svg'
    dependencies = ACTION_PATH / 'help-dependencies.svg'

    # Toolbar icons
    menu_manager = ACTION_PATH / 'menu-manager.svg'

    # Chart dialog template icons
    chart_pie_1_1 = CHARTS_PATH / 'chart_pie_1_1.svg'
    chart_ring_1_1 = CHARTS_PATH / 'chart_ring_1_1.svg'
    chart_line_1_1 = CHARTS_PATH / 'chart_line_1_1.svg'
    chart_polar_1_1 = CHARTS_PATH / 'chart_polar_1_1.svg'
    chart_area_1_1 = CHARTS_PATH / 'chart_area_1_1.svg'
    chart_column_1_1 = CHARTS_PATH / 'chart_column_1_1.svg'
    chart_column_1_2 = CHARTS_PATH / 'chart_column_1_2.svg'
    chart_bar_1_3 = CHARTS_PATH / 'chart_bar_1_3.svg'
    chart_scatter_1_1 = CHARTS_PATH / 'chart_scatter_1_1.svg'
    chart_bubble_1_1 = CHARTS_PATH / 'chart_bubble_1_1.svg'
    chart_boxplot_2_2 = CHARTS_PATH / 'chart_boxplot_2_2.svg'
    chart_histogram_1_1 = CHARTS_PATH / 'chart_histogram_1_1.svg'
    chart_histogram_1_4 = CHARTS_PATH / 'chart_histogram_1_4.svg'
    chart_scatterhist_1_1 = CHARTS_PATH/'chart_scatterhist_1_1.svg'
    chart_matrix_1_1 = CHARTS_PATH / 'chart_matrix_1_1.svg'
    chart_contour_1_2 = CHARTS_PATH / 'chart_contour_1_2.svg'
    chart_surface_2_1 = CHARTS_PATH / 'chart_surface_2_1.svg'


class IconConverter(type):
    """Meta class that provides QIcons for IconPaths icons"""

    def __getattr__(cls, name: str) -> QIcon:
        """Provides QIcons for icon names

        :param name: Icon name

        """

        return QIcon(str(getattr(IconPath, name)))


class Icon(metaclass=IconConverter):
    """Provides QIcons as attributes for all attributes of IconPaths"""
