#!/usr/bin/env python

# main.py
# qtdsexporter

# Created by M. Nasimul Haque.
# Copyright 2010, M. Nasimul Haque.

# This is a free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import sys

from PyQt4 import QtGui

from window import MainWindow

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
