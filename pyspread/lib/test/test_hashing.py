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
test_hashing
============

Unit tests for hashing.py

"""

import pytest
from ..hashing import genkey, sign, verify


KEYS = [genkey() for _ in range(100)]


def test_genkey():
    """Unit test for genkey"""

    keys = []

    for length in range(1, 128):
        keys.append(genkey(length))

    for i, key in enumerate(keys):
        assert len(key) == i + 1

    assert len(set(KEYS)) == len(KEYS)


param_test_sign_verify = [
    (b"Test", KEYS[0], b"Test", KEYS[0], True),
    (100*"\u2200".encode('utf-8'), KEYS[0], 100*"\u2200".encode('utf-8'),
     KEYS[0], True),
    (b"Test", KEYS[0], b"Test", KEYS[1], False),
    (b"Test", KEYS[0], b"TEST", KEYS[0], False),
    (b"Test", KEYS[0], b"TEST", KEYS[3], False),
    (b"", KEYS[0], b"", KEYS[3], False),
    (b"", KEYS[0], b"", KEYS[0], True),
    (b"Hello World\n"*100000, KEYS[1], b"Hello World\n"*100000, KEYS[1], True),
]


@pytest.mark.parametrize("data1, sigkey, data2, verkey, res",
                         param_test_sign_verify)
def test_sign_verify(data1, sigkey, data2, verkey, res):
    """Unit test for sign and verify"""

    signature = sign(data1, sigkey)
    assert verify(data2, signature, verkey) == res
