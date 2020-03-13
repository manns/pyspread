#  Copyright 2014-2014 Hans Meine <hans_meine@gmx.net>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""This module contains a wrapper around three different Qt python bindings.
It will dynamically decide which one to use:

* First, the environment variable QT_DRIVER is checked
  (may be one of 'PyQt5', 'PyQt4', 'PySide', 'PythonQt').
* If unset, previously imported binding modules are detected (in sys.modules).
* If no bindings are loaded, the environment variable QT_API is checked
  (used by ETS and ipython, may be 'pyside' or 'pyqt').

In order to have compatible behavior between the different bindings,
PyQt4 (if used) is configured as follows::

    sip.setapi("QString", 2)
    sip.setapi("QVariant", 2)

Furthermore, there is a 'getprop' function that solves the following
problem: PythonQt exports Qt properties as Python properties *and*
gives the precedence over getters with the same name.  Instead of
calling getters with parentheses (which must not be used in PythonQt,
but are required in PyQt and PySide), one may e.g. write
`getprop(widget.width)`.
"""

import sys, os

def getprop_PythonQt(prop):
    """getprop(property_or_getter)

    Used on getters that have the same name as a corresponding
    property.  For PythonQt, this version will just return the
    argument, which is assumed to be (the value of) a python property
    through which PythonQt exposes Qt properties."""
    return prop

def getprop_other(getter):
    """getprop(property_or_getter)

    Used on getters that have the same name as a corresponding
    property.  For Qt bindings other than PythonQt, this version will
    return the result of calling the argument, which is assumed to be
    a Qt getter function.  (With PythonQt, properties override getters
    and no calling must be done.)"""
    return getter()

class QtDriver(object):
    DRIVERS = ('PyQt5', 'PyQt4', 'PySide', 'PySide2', 'PythonQt')
    DEFAULT = 'PyQt5'
    
    @classmethod
    def detect_qt(cls):
        for drv in cls.DRIVERS:
            if drv in sys.modules:
                return drv
        if '_PythonQt' in sys.modules:
            return 'PythonQt'
        return None

    def name(self):
        return self._drv

    def getprop(self):
        return getprop_PythonQt if self._drv == 'PythonQt' else getprop_other

    def __init__(self, drv = os.environ.get('QT_DRIVER')):
        """Supports QT_API (used by ETS and ipython)"""
        if drv is None:
            drv = self.detect_qt()
        if drv is None:
            drv = os.environ.get('QT_API')
        if drv is None:
            drv = self.DEFAULT
        drv = {'pyside': 'PySide', 'pyside2': 'PySide2',
               'pyqt'  : 'PyQt4',  'pyqt5'  : 'PyQt5'}.get(drv, drv) # map ETS syntax
        assert drv in self.DRIVERS
        self._drv = drv

    @staticmethod
    def _initPyQt4():
        """initialize PyQt4 to be compatible with PySide"""
        if 'PyQt4.QtCore' in sys.modules:
            # too late to configure API
            pass
        else:
            import sip
            sip.setapi("QString", 2)
            sip.setapi("QVariant", 2)

    @staticmethod
    def requireCompatibleAPI():
        """If PyQt4's API should be configured to be compatible with PySide's
        (i.e. QString and QVariant should not be explicitly exported,
        cf. documentation of sip.setapi()), call this function to check that
        the PyQt4 was properly imported.  (It will always be configured this
        way by this module, but it could have been imported before we got a
        hand on doing so.)
        """
        if 'PyQt4.QtCore' in sys.modules:
            import sip
            for api in ('QVariant', 'QString'):
                if sip.getapi(api) != 2:
                    raise RuntimeError('%s API already set to V%d, but should be 2' % (api, sip.getapi(api)))
            
    def importMod(self, mod):
        if self._drv == 'PyQt4':
            self._initPyQt4()
        qt = __import__('%s.%s' % (self._drv, mod))
        return getattr(qt, mod)

    def __getattr__(self, name):
        if name.startswith('Qt'):
            return self.importMod(name)
        return super(QtDriver, self).__getattr__(name)
