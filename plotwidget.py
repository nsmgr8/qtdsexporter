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

from PyQt4 import QtGui, QtCore

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib import font_manager
import matplotlib.dates as mdates

import pymongo

import indicators

class PlotWidget(QtGui.QWidget):

    def __init__(self, parent=None, code=None, plots=None):
        super(PlotWidget, self).__init__(parent)
        if code:
            self.window().setWindowTitle(code)
        self.code = code
        self.plots = plots

        self.connection = pymongo.Connection()
        self.db = self.connection.qtdsexporter

        figure = Figure((5.0, 4.0))
        self.canvas = FigureCanvas(figure)
        self.canvas.window().setWindowTitle("Graph")
        FigureCanvas.setSizePolicy(self.canvas, QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)

        left, width = 0.1, 0.8
        rect1 = [left, 0.7, width, 0.2]
        rect2 = [left, 0.3, width, 0.4]
        rect3 = [left, 0.1, width, 0.2]

        self.axes1 = figure.add_axes(rect1)
        self.axes2 = figure.add_axes(rect2, sharex=self.axes1)
        self.axes3 = figure.add_axes(rect3, sharex=self.axes1)

        self.date_picker = QtGui.QDateEdit(datetime.datetime.today())
        self.date_picker.setDisplayFormat("MMM d, yyyy")
        label = QtGui.QLabel("Date:")
        label.setBuddy(self.date_picker)

        self.today = QtGui.QCheckBox("Today")

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.date_picker)
        hbox.addWidget(self.today)
        hbox.addStretch()

        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.canvas)
        vbox.addWidget(NavigationToolbar(self.canvas, self))
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.create_connections()

    def create_connections(self):
        self.connect(self.date_picker, QtCore.SIGNAL("dateChanged(const QDate &)"),
                     self.plot_graph)
        self.connect(self.today, QtCore.SIGNAL("stateChanged(int)"),
                     self.plot_today)

    def plot_today(self):
        check = self.today.checkState()
        if check == QtCore.Qt.Checked:
            self.date_picker.setDate(datetime.datetime.today())
            self.date_picker.setEnabled(False)
        elif check == QtCore.Qt.Unchecked:
            self.date_picker.setEnabled(True)

    def closeEvent(self, event):
        del self.plots[self.code]

    def plot_graph(self):
        self.axes1.cla()
        self.axes2.cla()
        self.axes3.cla()

        for ax in self.axes1, self.axes2, self.axes3:
            if ax != self.axes3:
                for label in ax.get_xticklabels():
                    label.set_visible(False)
            else:
                for label in ax.get_xticklabels():
                    label.set_rotation(40)
                    label.set_horizontalalignment('right')

            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

        from_ = self.date_picker.date()
        from_ = datetime.date(day=from_.day(), month=from_.month(),
                              year=from_.year())
        to = from_ + datetime.timedelta(days=1)
        from_ = from_.strftime("%Y%m%d")
        to = to.strftime("%Y%m%d")
        query = self.db.trades.find({'code': self.code, 'datetime': {'$gte':
                                     from_, '$lt': to}}).sort('datetime')
        trades = [(datetime.datetime.strptime(trade['datetime'], "%Y%m%d%H%M%S"),
                  float(trade['open'])) for trade in query]

        if len(trades) > 0:
            heads = ['DateTime', 'Open',]
            r = indicators.get_records(heads, trades)

            try:
                rsi = indicators.relative_strength(r.open)

                fillcolor = 'darkgoldenrod'
                textsize = 9

                self.axes1.plot(r.datetime, rsi, fillcolor)
                self.axes1.fill_between(r.datetime, rsi, 70, where=(rsi>=70), facecolor=fillcolor, edgecolor=fillcolor)
                self.axes1.fill_between(r.datetime, rsi, 30, where=(rsi<=30), facecolor=fillcolor, edgecolor=fillcolor)
            except:
                pass

            self.axes1.axhline(70, color=fillcolor)
            self.axes1.axhline(30, color=fillcolor)
            self.axes1.text(0.6, 0.9, '>70 = overbought', va='top',
                            transform=self.axes1.transAxes, fontsize=textsize)
            self.axes1.text(0.6, 0.1, '<30 = oversold', transform=self.axes1.transAxes, fontsize=textsize)
            self.axes1.set_ylim(0, 100)
            self.axes1.set_yticks([30,70])
            self.axes1.text(0.025, 0.95, 'RSI (14)', va='top',
                            transform=self.axes1.transAxes, fontsize=textsize)

            try:
                ma = indicators.moving_average(r.open, 10, type_='simple')
                self.axes2.plot(r.datetime, ma, color='blue', lw=2, label='MA (10)')
            except:
                pass

            try:
                ma = indicators.moving_average(r.open, 20, type_='simple')
                self.axes2.plot(r.datetime, ma, color='red', lw=2, label='MA (20)')
            except:
                pass

            self.axes2.plot(r.datetime, r.open, color='black', label='Open')

            props = font_manager.FontProperties(size=8)
            self.axes2.legend(loc='lower left', shadow=True, fancybox=True, prop=props)

            fillcolor = 'darkslategrey'
            nslow, nfast, nema = 26, 12, 9

            try:
                emaslow, emafast, macd = indicators.moving_average_convergence(r.open, nslow=nslow, nfast=nfast)
                ema9 = indicators.moving_average(macd, nema, type_='exponential')

                self.axes3.plot(r.datetime, macd, color='black', lw=2)
                self.axes3.plot(r.datetime, ema9, color='blue', lw=1)
                self.axes3.fill_between(r.datetime, macd-ema9, 0, alpha=0.5, facecolor=fillcolor, edgecolor=fillcolor)
            except:
                pass

            self.axes3.text(0.025, 0.95, 'MACD (%d, %d, %d)'%(nfast, nslow, nema), va='top',
                     transform=self.axes3.transAxes, fontsize=textsize)

        self.axes1.grid(True)
        self.axes2.grid(True)
        self.axes3.grid(True)
        self.canvas.draw()

