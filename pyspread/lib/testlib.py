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

testlib
=======

Provides helpers for unit tests

"""

from functools import wraps


def unit_test_dialog_override(func):
    """Exchanges return data if in unit test mode"""

    @wraps(func)
    def wrapper(dialog):
        """
        A wrapping function
        """
        if dialog.parent().unit_test:
            return dialog.parent().unit_test_data
        else:
            return func(dialog)
    return wrapper


#    @wraps(func)
#    def wrapper(dialog):
#        if dialog.parent.unit_test:
#            return dialog.parent.unit_test_data
#        else:
#            return func(dialog)
#    return wrapper
