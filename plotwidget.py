# plotwidget.py
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

import datetime
import csv
import cStringIO as StringIO

from PyQt4 import QtGui

from matplotlib import mlab

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

import pymongo
import numpy as np


class PlotWidget(QtGui.QWidget):

    def __init__(self, parent=None, code=None):
        super(PlotWidget, self).__init__(parent)
        if code:
            self.window().setWindowTitle(code)
        self.code = code

        self.connection = pymongo.Connection()
        self.db = self.connection.qtdsexporter

        figure = Figure((5.0, 4.0))
        self.canvas = FigureCanvas(figure)
        self.canvas.window().setWindowTitle("Graph")
        FigureCanvas.setSizePolicy(self.canvas, QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)

        plot_widget = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout(plot_widget)
        vbox.addWidget(self.canvas)
        vbox.addWidget(NavigationToolbar(self.canvas, plot_widget))
        self.setLayout(vbox)

        self.axes1 = figure.add_subplot(311)
        self.axes2 = figure.add_subplot(312)
        self.axes3 = figure.add_subplot(313)

        self.axes1.grid(True)

    def plot_graph(self):
        self.axes1.cla()
        self.axes2.cla()
        self.axes3.cla()

        from_ = datetime.datetime.today().date() - datetime.timedelta(days=7)
        from_ = from_.strftime("%Y%m%d")
        trades = [(datetime.datetime.strptime(trade['datetime'], "%Y%m%d%H%M%S"),
                  float(trade['open'])) for trade in self.db.trades.find({
                      'code': self.code, 'datetime': {'$gte': from_}})]

        if len(trades) > 0:
            csvfile = StringIO.StringIO()
            csvwriter = csv.writer(csvfile)
            heads = ['DateTime', 'Open',]
            csvwriter.writerow(heads)

            for row in trades:
                csvwriter.writerow(row)

            csvfile.seek(0)
            r = mlab.csv2rec(csvfile)
            csvfile.close()

            self.axes1.plot(r.datetime, r.open, 'ro')

        closes = [(datetime.datetime.strptime(close['date'], "%Y%m%d").date(),
                   float(close['open']), float(close['close']),
                   float(close['high']), float(close['low']))
                  for close in self.db.close.find({'code': self.code})]

        csvfile = StringIO.StringIO()
        csvwriter = csv.writer(csvfile)
        heads = ['DateTime', 'Open', 'Close', 'High', 'Low',]
        csvwriter.writerow(heads)

        for row in closes:
            csvwriter.writerow(row)

        csvfile.seek(0)
        r = mlab.csv2rec(csvfile)
        csvfile.close()

        deltas = np.zeros_like(r.open)
        deltas[1:] = np.diff(r.open)
        up = deltas>0
        self.axes2.vlines(r.datetime[up], r.low[up], r.high[up], color='black', label='_nolegend_')
        self.axes2.vlines(r.datetime[~up], r.low[~up], r.high[~up], color='blue', label='_nolegend_')
        self.axes2.plot(r.datetime, r.open, 'r')

        #self.axes2.vlines(r.datetime, r.high, r.low, 'b')
        self.axes3.plot(r.datetime, r.open, 'r')
        self.axes1.grid(True)
        self.canvas.draw()


