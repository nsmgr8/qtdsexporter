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
import datetime
import string

from PyQt4 import QtCore, QtGui, QtNetwork

import pymongo

from plotwidget import PlotWidget

class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.window().setWindowTitle("QtDSExporter")
        self.mdi = QtGui.QMdiArea()
        self.setCentralWidget(self.mdi)

        self.plots = {}

        self.connection = pymongo.Connection()
        self.db = self.connection.qtdsexporter

        self.nam = QtNetwork.QNetworkAccessManager(self)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50000)

        self.create_symbol_dock()
        self.load_symbols()
        self.create_status_bar()
        self.create_connections()

    def create_symbol_dock(self):
        self.dock = QtGui.QDockWidget("Symbols", self)
        self.symbol_window = QtGui.QListWidget(self.dock)
        self.symbol_window.window().setWindowTitle("Symbols")
        self.dock.setWidget(self.symbol_window)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)

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
        self.connect(self.symbol_window, QtCore.SIGNAL("doubleClicked("
            "const QModelIndex&)"), self.plot_graph)

    def load_symbols(self):
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

            data = self.reply.readAll()
            with open(fname, 'wb') as f:
                f.write(data)

            self.save_data(data)
            self.plot_graph()

            trade_at = datetime.datetime.strptime(fname[-23:-4],
                                                  "%Y-%m-%dT%H-%M-%S")
            msg = "Saved data at %s" % trade_at.isoformat()
        else:
            msg = "Error downloading data: %s" % str(status.toInt())

        self.status.setText(msg)

    def save_data(self, data):
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
                'datetime': d[1] + d[2],
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
                        self.save_data(f.read())

                    print("%s: [%d, %d, %d]" % (fname, self.db.trades.count(),
                                                self.db.close.count(),
                                                self.db.codes.count()))
            self.load_symbols()

    def plot_graph(self):
        try:
            code = unicode(self.symbol_window.currentItem().text())
        except Exception, e:
            print(e)
            return

        plot = self.plots.get(code, None)
        if not plot:
            plot = PlotWidget(code=code, plots=self.plots)
            self.mdi.addSubWindow(plot)
            self.plots[code] = plot
            plot.plot_graph()
            plot.show()

        for w in self.mdi.subWindowList():
            if w.widget() == plot:
                self.mdi.setActiveSubWindow(w)

