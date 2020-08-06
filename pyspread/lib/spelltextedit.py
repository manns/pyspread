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

# QPlainTextEdit With Inline Spell Check original code
#
# Original PyQt4 Version:
#   https://nachtimwald.com/2009/08/22/qplaintextedit-with-in-line-spell-check/
#
# Copyright 2009 John Schember
# Copyright 2018 Stephan Sokolow
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Python Syntaxt highlighter original code
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    (1) Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
#    (2) Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
#    (3)The name of the author may not be used to
#    endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


#  Enchant Highlighter from John Schember; Stephan Sokolow
#  MIT license --> GPL compatible

#  PythonHighlighter from David Boddie
#  Modified BSD license --> GPL compatible
"""

**Provides**

 * :func:`format`
 * :class:`LineNumberArea`
 * :class:`SpellTextEdit`
 * :class:`PythonEnchantHighlighter`


"""

from math import log10
import sys
from warnings import warn

try:
    import enchant
    from enchant import tokenize
    from enchant.errors import TokenizerNotFoundError
except ImportError:
    enchant = None

try:
    # pylint: disable=ungrouped-imports
    from enchant.utils import trim_suggestions
except ImportError:  # Older versions of PyEnchant as on *buntu 14.04
    # pylint: disable=unused-argument
    def trim_suggestions(word, suggs, maxlen, calcdist=None):
        """API Polyfill for earlier versions of PyEnchant."""

        # TODO: Make this actually do some sorting

        return suggs[:maxlen]


# pylint: disable=no-name-in-module
from PyQt5.Qt import Qt
from PyQt5.QtCore import QEvent, QRegExp, QSize, QRect
from PyQt5.QtGui import (QFocusEvent, QSyntaxHighlighter, QTextBlockUserData,
                         QTextCharFormat, QTextCursor, QColor, QFont,
                         QFontMetricsF, QPainter, QPalette)
from PyQt5.QtWidgets import (QAction, QActionGroup, QApplication, QMenu,
                             QPlainTextEdit, QWidget)


def format(color, style=''):
    """Return a QTextCharFormat with the given attributes."""

    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('blue'),
    'operator': format('red'),
    'brace': format('darkGray'),
    'defclass': format('black', 'bold'),
    'string': format('magenta'),
    'string2': format('darkMagenta'),
    'comment': format('darkGreen', 'italic'),
    'self': format('black', 'italic'),
    'numbers': format('brown'),
}


class LineNumberArea(QWidget):
    def __init__(self, parent: QPlainTextEdit):
        """

        :param parent: Editor in which the line numbers shall be displayed

        """
        super().__init__(parent)

        self.parent = parent

    def sizeHint(self):
        return QSize(self.parent.line_number_area_width(), 0)

    def paintEvent(self, event: QEvent):
        """Paint event called by parent"""

        painter = QPainter(self)
        palette = QPalette()

        background_color = palette.color(QPalette.Window)
        text_color = palette.color(QPalette.Text)

        painter.fillRect(event.rect(), background_color)

        block = self.parent.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.parent.contentOffset()
        top = self.parent.blockBoundingGeometry(block).translated(offset).top()
        bottom = top + self.parent.blockBoundingRect(block).height()

        height = self.parent.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(block_number + 1)
                painter.setPen(text_color)
                painter.drawText(0, top, self.width(), height, Qt.AlignRight,
                                 number)

            block = block.next()
            top = bottom
            bottom = top + self.parent.blockBoundingRect(block).height()
            block_number += 1


class SpellTextEdit(QPlainTextEdit):
    """QPlainTextEdit subclass which does spell-checking using PyEnchant"""

    # Clamping value for words like "regex" which suggest so many things that
    # the menu runs from the top to the bottom of the screen and spills over
    # into a second column.
    max_suggestions = 20
    spaces_per_tab = 4

    def __init__(self, parent=None, line_numbers=True):

        super().__init__()

        # If a <Tab> is present then it should be of width 4
        try:
            _distance = QFontMetricsF(self.font()).horizontalAdvance(" ")
        except AttributeError:
            # PyQt5 version < 5.11
            _distance = QFontMetricsF(self.font()).boundingRect(" ").width()

        self.setTabStopDistance(_distance * self.spaces_per_tab)

        # Line number area
        if line_numbers:
            self.line_number_area = LineNumberArea(self)
            self.blockCountChanged.connect(self.update_line_number_area_width)
            self.updateRequest.connect(self.update_line_number_area)
            self.update_line_number_area_width()

        # Start with a default dictionary based on the current locale.
        self.highlighter = PythonEnchantHighlighter(self.document())
        if enchant is not None:
            try:
                self.highlighter.setDict(enchant.Dict())
            except Exception as err:
                # There are some weird enchant issues on different platforms.
                # One of those has occured.
                warn(str(err), ImportWarning)

    def get_line_number_area_width(self) -> int:
        """Returns width of line number area"""

        margin = 3
        digit_width = self.fontMetrics().width('9')
        digits = int(log10(max(1, self.blockCount()))) + 1

        return margin + digit_width * digits

    def update_line_number_area_width(self):
        """Updates width of line_number_area"""

        self.setViewportMargins(self.get_line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Handle updates for line_number_area"""

        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(),
                                         self.line_number_area.width(),
                                         rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event: QEvent):
        """Overides QPlainTextEdit.resizeEvent for handling line_number_area"""

        super().resizeEvent(event)

        crect = self.contentsRect()
        line_number_area_rect = QRect(crect.left(), crect.top(),
                                      self.get_line_number_area_width(),
                                      crect.height())
        try:
            self.line_number_area.setGeometry(line_number_area_rect)
        except AttributeError:
            pass

    def keyPressEvent(self, event):
        """Overide to change tab into spaces_per_tab spaces"""

        if event.key() == Qt.Key_Tab:
            self.insertPlainText(" " * self.spaces_per_tab)
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Custom context menu handler to add a spelling suggestions submenu"""

        if enchant is None:
            return

        popup_menu = self.createSpellcheckContextMenu(event.pos())
        popup_menu.exec_(event.globalPos())

        # Fix bug observed in Qt 5.2.1 on *buntu 14.04 LTS where:
        # 1. The cursor remains invisible after closing the context menu
        # 2. Keyboard input causes it to appear, but it doesn't blink
        # 3. Switching focus away from and back to the window fixes it
        self.focusInEvent(QFocusEvent(QEvent.FocusIn))

    def createSpellcheckContextMenu(self, pos):
        """Create and return an augmented default context menu.

        This may be used as an alternative to the QPoint-taking form of
        ``createStandardContextMenu`` and will work on pre-5.5 Qt.
        """

        try:  # Recommended for Qt 5.5+ (Allows contextual Qt-provided entries)
            menu = self.createStandardContextMenu(pos)
        except TypeError:  # Before Qt 5.5
            menu = self.createStandardContextMenu()

        # Add a submenu for setting the spell-check language
        menu.addSeparator()
        menu.addMenu(self.createLanguagesMenu(menu))
        menu.addMenu(self.createFormatsMenu(menu))

        # Try to retrieve a menu of corrections for the right-clicked word
        spell_menu = self.createCorrectionsMenu(
            self.cursorForMisspelling(pos), menu)

        if spell_menu:
            menu.insertSeparator(menu.actions()[0])
            menu.insertMenu(menu.actions()[0], spell_menu)

        return menu

    def createCorrectionsMenu(self, cursor, parent=None):
        """Create and return a menu for correcting the selected word."""

        if not cursor:
            return None

        text = cursor.selectedText()
        suggests = trim_suggestions(text,
                                    self.highlighter.dict().suggest(text),
                                    self.max_suggestions)

        spell_menu = QMenu('Spelling Suggestions', parent)
        for word in suggests:
            action = QAction(word, spell_menu)
            action.setData((cursor, word))
            spell_menu.addAction(action)

        # Only return the menu if it's non-empty
        if spell_menu.actions():
            spell_menu.triggered.connect(self.cb_correct_word)
            return spell_menu

        return None

    def createLanguagesMenu(self, parent=None):
        """Create and return a menu for selecting the spell-check language."""

        try:
            curr_lang = self.highlighter.dict().tag
        except AttributeError:
            curr_lang = None

        lang_menu = QMenu("Language", parent)
        lang_actions = QActionGroup(lang_menu)

        for lang in enchant.list_languages():
            action = lang_actions.addAction(lang)
            action.setCheckable(True)
            action.setChecked(lang == curr_lang)
            action.setData(lang)
            lang_menu.addAction(action)

        lang_menu.triggered.connect(self.cb_set_language)
        return lang_menu

    def createFormatsMenu(self, parent=None):
        """Create and return a menu for selecting the spell-check language."""

        fmt_menu = QMenu("Format", parent)
        fmt_actions = QActionGroup(fmt_menu)

        curr_format = self.highlighter.chunkers()
        for name, chunkers in (('Text', []), ('HTML', [tokenize.HTMLChunker])):
            action = fmt_actions.addAction(name)
            action.setCheckable(True)
            action.setChecked(chunkers == curr_format)
            action.setData(chunkers)
            fmt_menu.addAction(action)

        fmt_menu.triggered.connect(self.cb_set_format)
        return fmt_menu

    def cursorForMisspelling(self, pos):
        """Return a cursor selecting the misspelled word at ``pos`` or ``None``

        This leverages the fact that QPlainTextEdit already has a system for
        processing its contents in limited-size blocks to keep things fast.
        """

        cursor = self.cursorForPosition(pos)
        misspelled_words = getattr(cursor.block().userData(), 'misspelled', [])

        # If the cursor is within a misspelling, select the word
        for (start, end) in misspelled_words:
            if start <= cursor.positionInBlock() <= end:
                block_pos = cursor.block().position()

                cursor.setPosition(block_pos + start, QTextCursor.MoveAnchor)
                cursor.setPosition(block_pos + end, QTextCursor.KeepAnchor)
                break

        if cursor.hasSelection():
            return cursor
        else:
            return None

    def cb_correct_word(self, action):  # pylint: disable=no-self-use
        """Event handler for 'Spelling Suggestions' entries."""

        cursor, word = action.data()

        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()

    def cb_set_language(self, action):
        """Event handler for 'Language' menu entries."""

        lang = action.data()
        self.highlighter.setDict(enchant.Dict(lang))

    def cb_set_format(self, action):
        """Event handler for 'Language' menu entries."""

        chunkers = action.data()
        self.highlighter.setChunkers(chunkers)
        # TODO: Emit an event so this menu can trigger other things


class PythonEnchantHighlighter(QSyntaxHighlighter):
    """QSyntaxHighlighter subclass which consults a PyEnchant dictionary"""

    if enchant is not None:
        tokenizer = None
        token_filters = (tokenize.EmailFilter, tokenize.URLFilter)

    enable_enchant = False

    # Define the spellcheck style once and just assign it as necessary
    # XXX: Does QSyntaxHighlighter.setFormat handle keeping this from
    #      clobbering styles set in the data itself?
    err_format = QTextCharFormat()
    err_format.setUnderlineColor(Qt.red)
    err_format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)

    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        r'\+', '-', r'\*', '/', '//', r'\%', r'\*\*',
        # In-place
        r'\+=', '-=', r'\*=', '/=', r'\%=',
        # Bitwise
        r'\^', r'\|', r'\&', r'\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        r'\{', r'\}', r'\(', r'\)', r'\[', r'\]',
    ]

    def __init__(self, *args):
        QSyntaxHighlighter.__init__(self, *args)

        # Initialize private members
        self._sp_dict = None
        self._chunkers = []

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword']) for w in self.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator']) for o in self.operators]
        rules += [(r'%s' % b, 0, STYLES['brace']) for b in self.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0,
             STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """

        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                try:
                    text_length = text.length()
                except AttributeError:
                    text_length = len(text)
                length = text_length - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False

    def chunkers(self):
        """Gets the chunkers in use"""

        return self._chunkers

    def dict(self):
        """Gets the spelling dictionary in use"""

        return self._sp_dict

    def setChunkers(self, chunkers):
        """Sets the list of chunkers to be used"""

        self._chunkers = chunkers
        self.setDict(self.dict())
        # FIXME: Revert self._chunkers on failure to ensure consistent state

    def setDict(self, sp_dict):
        """Sets the spelling dictionary to be used"""
        if enchant is None:
            return

        try:
            self.tokenizer = tokenize.get_tokenizer(sp_dict.tag,
                                                    chunkers=self._chunkers,
                                                    filters=self.token_filters)
        except TokenizerNotFoundError:
            # Fall back to the "good for most euro languages" English tokenizer
            self.tokenizer = tokenize.get_tokenizer(
                chunkers=self._chunkers, filters=self.token_filters)
        self._sp_dict = sp_dict

        self.rehighlight()

    def highlightBlock_enchant(self, text):
        """Method for pyenchant spell checker"""

        if not self._sp_dict:
            return

        # Build a list of all misspelled words and highlight them
        misspellings = []
        for (word, pos) in self.tokenizer(text):
            if not self._sp_dict.check(word):
                self.setFormat(pos, len(word), self.err_format)
                misspellings.append((pos, pos + len(word)))

        # Store the list so the context menu can reuse this tokenization pass
        # (Block-relative values so editing other blocks won't invalidate them)
        data = QTextBlockUserData()
        data.misspelled = misspellings
        self.setCurrentBlockUserData(data)

    def highlightBlock_python(self, text):
        """Method for Python highlighter"""

        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def highlightBlock(self, text):
        """Overridden QSyntaxHighlighter method to apply the highlight"""

        self.highlightBlock_python(text)

        if enchant is not None and self.enable_enchant:
            self.highlightBlock_enchant(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    spellEdit = SpellTextEdit()
    spellEdit.show()

    sys.exit(app.exec_())
