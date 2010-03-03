#!/usr/bin/env python

import sys

from PyQt4 import QtGui

from window import MainWindow

if __name__ == '__main__':
    app = QtGui.QApplication([''])

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
