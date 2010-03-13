# window.py
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

import os
import csv
import datetime
import cStringIO as StringIO
import string

from PyQt4 import QtCore, QtGui, QtNetwork

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

import numpy as np
import matplotlib.mlab as mlab

import pymongo

class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.window().setWindowTitle("QtDSExporter")
        self.mdi = QtGui.QMdiArea()
        self.setCentralWidget(self.mdi)

        self.connection = pymongo.Connection()
        self.db = self.connection.qtdsexporter.dse

        self.nam = QtNetwork.QNetworkAccessManager(self)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50000)

        self.symbol_window = QtGui.QListWidget()
        self.symbol_window.window().setWindowTitle("Symbols")
        self.mdi.addSubWindow(self.symbol_window)

        self.populate_widgets()

        figure = Figure((5.0, 4.0))
        self.canvas = FigureCanvas(figure)
        self.canvas.window().setWindowTitle("Graph")
        FigureCanvas.setSizePolicy(self.canvas, QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)

        plot_widget = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout(plot_widget)
        vbox.addWidget(self.canvas)
        vbox.addWidget(NavigationToolbar(self.canvas, plot_widget))

        left, width = 0.1, 0.8
        rect1 = [left, 0.7, width, 0.2]
        rect2 = [left, 0.3, width, 0.4]
        rect3 = [left, 0.1, width, 0.2]

        self.axes1 = figure.add_axes(rect1)
        self.axes2 = figure.add_axes(rect2)#, sharex=self.axes1)
        self.axes3 = figure.add_axes(rect3)#, sharex=self.axes1)

        self.axes1.grid(True)
        self.mdi.addSubWindow(plot_widget)

        self.create_status_bar()
        self.create_connections()

    def create_status_bar(self):
        self.status = QtGui.QLabel("Ready")
        self.fetch_check = QtGui.QCheckBox("Fetch new data")

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.status)
        hbox1.addStretch()
        hbox1.addWidget(self.fetch_check)

        widget = QtGui.QWidget()
        widget.setLayout(hbox1)
        self.statusBar().addWidget(widget)


    def create_connections(self):
        self.connect(self.fetch_check, QtCore.SIGNAL("stateChanged(int)"),
                     self.fetch)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.make_request)
        self.connect(self.symbol_window, QtCore.SIGNAL("currentItemChanged ("
            "QListWidgetItem*, QListWidgetItem*)"), self.plot_graph)

    def populate_widgets(self):
        self.symbol_window.clear()
        self.symbol_window.addItems(sorted([code['symbol'] for code in
                                            self.db.codes.find()]))

    def fetch(self):
        check = self.fetch_check.checkState()
        if check == QtCore.Qt.Checked:
            self.start_fetching()
        elif check == QtCore.Qt.Unchecked:
            self.stop_fetching()


    def start_fetching(self):
        self.timer.start()
        self.make_request()

    def stop_fetching(self):
        self.timer.stop()
        self.status.setText("Ready")

    def make_request(self):
        self.status.setText("Requesting new data...")

        url = QtCore.QUrl("http://dsecse.latest.nsmgr8.appspot.com/dse")
        self.reply = self.nam.get(QtNetwork.QNetworkRequest(url))
        self.connect(self.reply, QtCore.SIGNAL("readyRead()"), self.finished)

    def finished(self):
        status = self.reply.attribute(QtNetwork.QNetworkRequest
                                      .HttpStatusCodeAttribute)
        if(status.toInt() == (200, True)):
            fname = str(self.reply.rawHeader("Content-Disposition"))
            csv_folder = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "csv")
            if not os.path.isdir(csv_folder):
                os.mkdir(csv_folder)
            fname = os.path.join(csv_folder,
                                 fname[fname.find("dse"):-1].replace(':', '-'))

            trade_at = datetime.datetime.strptime(fname[-23:-4],
                                                  "%Y-%m-%dT%H-%M-%S")

            data = self.reply.readAll()
            with open(fname, 'wb') as f:
                f.write(data)

            self.save_data(trade_at, data)
            self.plot_graph()

            msg = "Saved data at %s" % trade_at.isoformat()
        else:
            msg = "Error downloading data: %s" % str(status.toInt())

        self.status.setText(msg)

    def save_data(self, trade_at, data):
        day_start = '11:00:00'
        day_end = '15:06:00'
        data = str(data).split('\r\n')[1:]
        for d in data:
            d = map(string.strip, d.split(','))
            if len(d) < 11:
                print "malformed data:", d
                continue

            if d[2] < day_start or d[2] > day_end:
                print "out of trading time:", d[2]
                continue

            d[1] = d[1][-4:] + d[1][:2] + d[1][3:5]
            d[2] = d[2].replace(':', '')

            self.db.codes.insert({
                '_id': d[0],
                'symbol': d[0],
            })

            self.db.trades.insert({
                '_id': '_'.join(d[:3]),
                'code': d[0],
                'date': d[1],
                'time': d[2],
                'open': d[3],
            })

            if d[6] != '0':
                self.db.close.insert({
                    '_id': '_'.join(d[:2]),
                    'code': d[0],
                    'date': d[1],
                    'open': d[3],
                    'high': d[4],
                    'low': d[5],
                    'close': d[6],
                    'last': d[7],
                    'trade': d[9],
                    'volume': d[10],
                })

    def load_data(self):
        dirname = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'csv')
        for dir, dirs, fnames in os.walk(dirname):
            for f in fnames:
                QtGui.QApplication.processEvents()
                if f.endswith(".csv"):
                    fname = os.path.join(dir, f)
                    trade_at = datetime.datetime.strptime(fname[-23:-4],
                                                          "%Y-%m-%dT%H-%M-%S")

                    with open(fname, 'r') as f:
                        self.save_data(trade_at, f.read())

                    print("%s: %d" % (fname, self.db.trades.count()))
            self.populate_widgets()

    def plot_graph(self):
        self.axes1.cla()
        self.axes2.cla()
        self.axes3.cla()

        try:
            code = unicode(self.symbol_window.currentItem().text())
        except:
            return

        from_ = datetime.datetime.today().date() - datetime.timedelta(days=7)
        from_ = from_.strftime("%Y%m%d")
        trades = [(datetime.datetime.strptime(trade['date']+trade['time'], "%Y%m%d%H%M%S"),
                  float(trade['open'])) for trade in self.db.trades.find({
                      'code': code, 'date': {'$gte': from_}})]

        if len(trades) == 0:
            return

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
                   close['open'], close['close'], close['high'], close['low'])
                  for close in self.db.close.find({'code': code})]

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

        #self.axes2.vlines(r.datetime, r.high, r.low, 'b')
        self.axes3.plot(r.datetime, r.open, 'r')
        self.axes1.grid(True)
        self.canvas.draw()

