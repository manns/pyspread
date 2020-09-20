#!/usr/bin/env python
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
test_csv
========

Unit tests for csv.py

"""

import datetime
from pathlib import Path

import pytest

from ..csv import sniff, get_header, csv_reader, convert


TESTPATH = Path(__file__).parent


param_sniff = [
    (TESTPATH / 'valid1.csv', True, ',', 0, 0, '"', "\r\n", 0),
    (TESTPATH / 'valid2.csv', True, '\t', 0, 0, '"', "\r\n", 0),
    (TESTPATH / 'valid3.csv', True, '\t', 0, 0, '"', "\r\n", 0),
    (TESTPATH / 'valid4.csv', True, ',', 0, 0, '"', "\r\n", 0),
]


@pytest.mark.parametrize(
    "filepath, hasheader, delimiter, doublequote, quoting, quotechar, "
    "lineterminator, skipinitialspace", param_sniff)
def test_sniff(filepath, hasheader, delimiter, doublequote, quoting, quotechar,
               lineterminator, skipinitialspace):
    """Unit test for sniff"""

    dialect = sniff(filepath, 1024)
    assert dialect.hasheader == hasheader
    assert dialect.delimiter == delimiter
    assert dialect.doublequote == doublequote
    assert dialect.quoting == quoting
    assert dialect.quotechar == quotechar
    assert dialect.lineterminator == lineterminator
    assert dialect.skipinitialspace == skipinitialspace


param_get_header = [
    (TESTPATH / 'valid1.csv', ["a", "b", "c"]),
]


@pytest.mark.parametrize("filepath, header", param_get_header)
def test_get_header(filepath, header):
    """Unit test for get_first_line"""

    dialect = sniff(filepath, 1024)
    with open(filepath) as csvfile:
        __header = get_header(csvfile, dialect)

    assert __header == header


def test_csv_reader():
    """Unit test for csv_reader"""

    filepath = TESTPATH / 'valid1.csv'
    dialect = sniff(filepath, 1024)
    result = [["1", "2", "3"], ["4", "5", "6"]]

    with open(filepath) as csvfile:
        reader = csv_reader(csvfile, dialect)
        for line, resline in zip(reader, result):
            assert line == resline


param_convert = [
    ('12', 'object', '12'),
    ('12', 'str', "'12'"),
    ('12', 'bool', 'True'),
    ('12', 'bytes', "'12'"),
    ('12', 'complex', "(12+0j)"),
    ('12', 'int', "12"),
    ('12', 'float', "12.0"),
    ('12.0', 'repr', "'12.0'"),
    ('12.0', 'object', "12.0"),
    ('2000-1-1', 'date', repr(datetime.date(2000, 1, 1))),
    ('1995-02-05 00:00', 'datetime',
     repr(datetime.datetime(1995, 2, 5, 0, 0))),
    ('23:59:59', 'time', repr(datetime.time(23, 59, 59))),
]


@pytest.mark.parametrize("string, digest_type, res", param_convert)
def test_convert(string, digest_type, res):
    """Unit test for convert"""

    assert convert(string, digest_type) == res
