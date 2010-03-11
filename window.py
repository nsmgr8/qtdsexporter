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

from PyQt4 import QtCore, QtGui, QtNetwork

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from models import *

class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.window().setWindowTitle("QtDSExporter")
        self.mdi = QtGui.QMdiArea()
        self.setCentralWidget(self.mdi)

        setup_all()
        create_all()

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
        self.axes = figure.add_subplot(111)
        self.axes.grid(True)
        self.mdi.addSubWindow(self.canvas)

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
        codes = Code.query.order_by(Code.code).all()
        self.symbol_window.clear()
        self.symbol_window.addItems([code.code for code in codes])

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
        data = str(data).split('\r\n')[1:]
        for d in data:
            d = d.split(',')
            if len(d) < 11:
                continue
            d = map(unicode, d)

            try:
                code = Code.query.filter_by(code=d[0]).one()
            except:
                code = Code(code=d[0])

            try:
                trade = Trade.query.filter_by(code=code,
                                              trade_at=trade_at).one()
            except:
                Trade(code=code, trade_at=trade_at, open=float(d[3]),
                      trade=int(d[9]), volume=int(d[10]))

            try:
                close = Close.query.filter_by(code=code,
                                              day=trade_at.date()).one()
                close.close = float(d[6])
            except:
                Close(code=code, day=trade_at.date(), close=float(d[6]))

            try:
                yesterday = trade_at.date() - datetime.timedelta(days=1)
                Close.query.filter_by(code=code, day=yesterday).one()
            except Exception, e:
                Close(code=code, day=yesterday, close=float(d[7]))

        session.commit()

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

                    with open(fname, 'r') as csv:
                        self.save_data(trade_at, csv.read())

                    print("%s: %d" % (fname, Trade.query.count()))

    def plot_graph(self):
        code = unicode(self.symbol_window.currentItem().text())
        code = Code.get_by(code=code)
        trades = Trade.get_by_code(code).order_by(Trade.trade_at).all()

        if len(trades) == 0:
            self.axes.cla()
            return

        times = [trade.trade_at for trade in trades]
        opens = [trade.open for trade in trades]

        date = datetime.datetime.now()
        day_before = date.date() - datetime.timedelta(days=1)

        close = Close.query.filter_by(code=code, day=date.date()).one()
        last = Close.query.filter_by(code=code, day=day_before).one()
        num_trades = trades[-1].trade
        volume = trades[-1].volume

        high, low = max(opens), min(opens)
        texts = (
            ("Code: %s", code.code),
            ("High: %.2f", high),
            ("Low: %.2f", low),
            ("Close: %.2f", close.close),
            ("Last: %.2f", last.close),
            ("Change: %+.2f", close.close - last.close),
            ("Change: %+.2f%%", (close.close - last.close) / last.close *
             100),
            ("Trade: %d", num_trades),
            ("Volume: %d", volume),
        )

        text = ' '.join([t[0] % t[1] for t in texts])

        self.axes.cla()
        self.axes.plot(times, opens, 'r')
        self.axes.text(0.025, 0.95, text, transform=self.axes.transAxes)
        self.axes.grid(True)
        self.canvas.draw()

