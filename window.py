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

from models import *
from scene import PlotScene


class MainWindow(QtGui.QWidget):

    DAY_START = 10
    DAY_END = 18
    HOURS = DAY_END - DAY_START
    TIME_PIXELS = 60 * HOURS
    PLOT_PIXELS = 270  # divisible by 9

    TIME_TICK = TIME_PIXELS / HOURS
    PLOT_TICK = PLOT_PIXELS / 9

    PLOT_PADDING = 20

    PLOT_LEFT = 10
    PLOT_RIGHT = TIME_PIXELS + PLOT_LEFT + 2 * PLOT_PADDING
    PLOT_TOP = 10
    PLOT_BOTTOM = PLOT_PIXELS + PLOT_TOP + 2 * PLOT_PADDING

    SCENE_WIDTH = PLOT_RIGHT + 50
    SCENE_HEIGHT = PLOT_BOTTOM + 30

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        setup_all()
        create_all()

        self.nam = QtNetwork.QNetworkAccessManager(self)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50000)

        self.create_layout()
        self.create_connections()
        self.populate_widgets()

    def create_layout(self):
        trade_label = QtGui.QLabel("Trade code:")
        self.trade_combo = QtGui.QComboBox()
        trade_label.setBuddy(self.trade_combo)

        date_label = QtGui.QLabel("Date:")
        self.date_picker = QtGui.QDateEdit()
        self.date_picker.setDisplayFormat("MMM d, yyyy")
        self.date_picker.setDate(QtCore.QDate.currentDate())
        date_label.setBuddy(self.date_picker)

        ind_label = QtGui.QLabel("Indicator:")
        self.ind_combo = QtGui.QComboBox()
        ind_label.setBuddy(self.ind_combo)
        self.ind_combo.addItems(['Open', 'Trade', 'Volume'])

        self.live_check = QtGui.QCheckBox("Live graph")
        self.graph_button = QtGui.QPushButton("Graph data")
        self.fetch_button = QtGui.QPushButton("Start fetching")
        self.stop_button = QtGui.QPushButton("Stop fetching")
        self.stop_button.setEnabled(False)

        self.scene = PlotScene(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT);
        self.scene.setBackgroundBrush(QtGui.QColor(0xFF, 0xFF, 0xEE))
        self.scene.setPlotProps(self.PLOT_PADDING, self.PLOT_LEFT, self.PLOT_TOP,
                                self.PLOT_RIGHT, self.PLOT_BOTTOM)
        self.canvas = QtGui.QGraphicsView(self.scene)
        self.canvas.setCursor(QtCore.Qt.CrossCursor)

        self.status = QtGui.QLabel("Ready")
        self.coords = QtGui.QLabel()
        self.coords.setAlignment(QtCore.Qt.AlignRight)
        self.scene.setStatusLabel(self.coords)

        hbox_trade = QtGui.QHBoxLayout()
        hbox_trade.addWidget(trade_label)
        hbox_trade.addWidget(self.trade_combo)

        hbox_date = QtGui.QHBoxLayout()
        hbox_date.addWidget(ind_label)
        hbox_date.addWidget(self.ind_combo)

        vbox1 = QtGui.QVBoxLayout()
        vbox1.addLayout(hbox_trade)
        vbox1.addLayout(hbox_date)

        hbox_ind = QtGui.QHBoxLayout()
        hbox_ind.addWidget(date_label)
        hbox_ind.addWidget(self.date_picker)
        hbox_ind.addStretch()

        hbox_graph = QtGui.QHBoxLayout()
        hbox_graph.addWidget(self.graph_button)
        hbox_graph.addWidget(self.live_check)
        hbox_graph.addStretch()

        vbox2 = QtGui.QVBoxLayout()
        vbox2.addLayout(hbox_ind)
        vbox2.addLayout(hbox_graph)

        vbox_buttons = QtGui.QVBoxLayout()
        vbox_buttons.addWidget(self.fetch_button)
        vbox_buttons.addWidget(self.stop_button)

        grid = QtGui.QGridLayout(self)
        grid.addLayout(vbox1, 0, 0)
        grid.addLayout(vbox2, 0, 1)
        grid.addLayout(vbox_buttons, 0, 3)
        grid.addWidget(self.canvas, 1, 0, 1, 4)
        grid.addWidget(self.status, 2, 0, 1, 3)
        grid.addWidget(self.coords, 2, 3)

    def create_connections(self):
        self.connect(self.graph_button, QtCore.SIGNAL("clicked()"),
                     self.plot_graph)
        self.connect(self.fetch_button, QtCore.SIGNAL("clicked()"),
                     self.start_fetching)
        self.connect(self.stop_button, QtCore.SIGNAL("clicked()"),
                     self.stop_fetching)
        self.connect(self.live_check, QtCore.SIGNAL("stateChanged(int)"),
                     self.live_plot)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.make_request)

    def populate_widgets(self):
        codes = Code.query.order_by(Code.code).all()
        self.trade_combo.clear()
        self.trade_combo.addItems([code.code for code in codes])

    def start_fetching(self):
        self.fetch_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.timer.start()
        self.make_request()

    def stop_fetching(self):
        self.fetch_button.setEnabled(True)
        self.stop_button.setEnabled(False)

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

            msg = "Saved data at %s" % trade_at.isoformat()

            if self.trade_combo.currentText() == "":
                self.populate_widgets()

            if self.live_check.checkState() == QtCore.Qt.Checked:
                self.plot_graph()
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
                close.close = float(d[4])
            except:
                Close(code=code, day=trade_at.date(), close=float(d[4]))

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
        code = Code.get_by(code=unicode(self.trade_combo.currentText()))
        indicator = unicode(self.ind_combo.currentText())
        date = self.date_picker.date()
        date = datetime.datetime(day=date.day(), month=date.month(),
                                 year=date.year())

        trades = Trade.get_by_code(code, date).order_by(Trade.trade_at).all()

        NO_DATA_MSG = "No data available for %s:%s at %s" % (code.code,
                                                             indicator,
                                                             date.isoformat())
        if len(trades) == 0:
            self.scene.clear()
            self.scene.addText(NO_DATA_MSG)
            return

        indexes = {
            'Open': lambda x: x.open,
            'Trade': lambda x: x.trade,
            'Volume': lambda x: x.volume,
        }

        times = []
        index = []
        for trade in trades:
            times.append(trade.trade_at.minute + (trade.trade_at.hour -
                         self.DAY_START) * 60 + self.PLOT_PADDING +
                         self.PLOT_LEFT)
            index.append(indexes[indicator](trade))

        self.scene.clear()
        try:
            max_index = max(index)
            min_index = min(index)
            if max_index == min_index:
                min_index = 0

            self.scene.setScales(self.DAY_START, min_index, max_index)

            points = zip(times, map(lambda x: self.PLOT_BOTTOM -
                                    self.PLOT_PADDING - self.PLOT_PIXELS *
                                    (x - min_index) / (max_index - min_index),
                                    index))

            path = QtGui.QPainterPath()
            path.moveTo(points[0][0], points[0][1])
            for p in points:
                path.lineTo(p[0], p[1])

            self.draw_time_axis()
            self.draw_value_axis(min_index, max_index)
            pathitem = self.scene.addPath(path)
            pathitem.setPen(QtGui.QPen(QtGui.QColor("red")))
            self.scene.plotted = True
        except:
            self.scene.plotted = False
            self.scene.addText(NO_DATA_MSG)

    def draw_time_axis(self):
        self.scene.addLine(QtCore.QLineF(self.PLOT_LEFT, self.PLOT_TOP,
                                         self.PLOT_RIGHT, self.PLOT_TOP))
        self.scene.addLine(QtCore.QLineF(self.PLOT_LEFT, self.PLOT_BOTTOM,
                                         self.PLOT_RIGHT, self.PLOT_BOTTOM))

        for i in range(self.PLOT_LEFT+self.PLOT_PADDING, self.PLOT_RIGHT,
                       self.TIME_TICK):
            tick = self.scene.addLine(i, self.PLOT_TOP, i, self.PLOT_BOTTOM)
            tick.setPen(QtGui.QPen(QtGui.QColor(0x35, 0xFF, 0xAA, 100)))
            text = QtGui.QGraphicsTextItem("%02d:00" % (i / 60 + self.DAY_START))
            text.setPos(i - 20, self.PLOT_BOTTOM)
            self.scene.addItem(text)

    def draw_value_axis(self, minx, maxx):
        self.scene.addLine(QtCore.QLineF(self.PLOT_LEFT, self.PLOT_TOP,
                                         self.PLOT_LEFT, self.PLOT_BOTTOM))
        self.scene.addLine(QtCore.QLineF(self.PLOT_RIGHT, self.PLOT_TOP,
                                         self.PLOT_RIGHT, self.PLOT_BOTTOM))

        dx = (maxx - minx)
        for i in range(self.PLOT_TOP+self.PLOT_PADDING, self.PLOT_BOTTOM,
                       self.PLOT_TICK):
            tick = self.scene.addLine(self.PLOT_LEFT, i, self.PLOT_RIGHT, i)
            tick.setPen(QtGui.QPen(QtGui.QColor(0xAA, 0xAA, 0xAA, 100)))

            y = (maxx + minx) - (dx * (i - (self.PLOT_TOP + self.PLOT_PADDING))
                                 / self.PLOT_PIXELS + minx)
            text = QtGui.QGraphicsTextItem("%.0f" % y)
            text.setPos(self.PLOT_RIGHT, i-10)
            self.scene.addItem(text)

    def live_plot(self):
        check = self.live_check.checkState()
        if check == QtCore.Qt.Checked:
            self.date_picker.setDate(QtCore.QDate.currentDate())
            self.date_picker.setEnabled(False)
            self.plot_graph()
        elif check == QtCore.Qt.Unchecked:
            self.date_picker.setEnabled(True)

