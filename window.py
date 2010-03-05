import os
import datetime

from PyQt4 import QtCore, QtGui, QtNetwork

from models import *


class MainWindow(QtGui.QDialog):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        setup_all()
        create_all()

        self.nam = QtNetwork.QNetworkAccessManager(self)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(6000)

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

        self.graph_button = QtGui.QPushButton("Graph data")
        self.fetch_button = QtGui.QPushButton("Start fetching")
        self.stop_button = QtGui.QPushButton("Stop fetching")
        self.stop_button.setEnabled(False)

        self.scene = QtGui.QGraphicsScene(0, 0, 700, 320);
        canvas = QtGui.QGraphicsView(self.scene)

        self.status = QtGui.QLabel("Ready")

        hbox_trade = QtGui.QHBoxLayout()
        hbox_trade.addWidget(trade_label)
        hbox_trade.addWidget(self.trade_combo)

        hbox_date = QtGui.QHBoxLayout()
        hbox_date.addWidget(date_label)
        hbox_date.addWidget(self.date_picker)

        vbox1 = QtGui.QVBoxLayout()
        vbox1.addLayout(hbox_trade)
        vbox1.addLayout(hbox_date)

        hbox_ind = QtGui.QHBoxLayout()
        hbox_ind.addWidget(ind_label)
        hbox_ind.addWidget(self.ind_combo)
        hbox_ind.addStretch()

        hbox_graph = QtGui.QHBoxLayout()
        hbox_graph.addWidget(self.graph_button)
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
        grid.addWidget(canvas, 1, 0, 1, 4)
        grid.addWidget(self.status, 2, 0, 1, 4)

    def create_connections(self):
        self.connect(self.graph_button, QtCore.SIGNAL("clicked()"),
                     self.plot_graph)
        self.connect(self.fetch_button, QtCore.SIGNAL("clicked()"),
                     self.start_fetching)
        self.connect(self.stop_button, QtCore.SIGNAL("clicked()"),
                     self.stop_fetching)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.make_request)

    def populate_widgets(self):
        codes = Code.query.order_by(Code.code).all()
        self.trade_combo.addItems([code.code for code in codes])
        self.ind_combo.addItems(['Open', 'Close', 'Trade', 'Volume'])

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
            fname = os.path.join(csv_folder, fname[fname.find("dse"):-1]) \
                    .replace(':', '-')

            trade_at = datetime.datetime.strptime(fname[-23:-4],
                                                  "%Y-%m-%dT%H-%M-%S")

            data = self.reply.readAll()
            with open(fname, 'w') as f:
                f.write(data)

            self.save_data(trade_at, data)

            msg = "Saved data at %s" % trade_at.isoformat()
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
                Trade(code=code, trade_at=trade_at,
                      open=float(d[3]), close=float(d[6]),
                      high=float(d[4]), low=float(d[5]),
                      last=float(d[7]), change=float(d[8]),
                      trade=int(d[9]), volume=int(d[10]))

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

        if len(trades) == 0:
            self.scene.clear()
            self.scene.addText("No data available")
            return

        indexes = {
            'Open': lambda x: x.open,
            'Close': lambda x: x.close,
            'Trade': lambda x: x.trade,
            'Volume': lambda x: x.volume,
        }

        day_start = 7 * 60
        day_end = 18 * 60

        times = []
        index = []
        for trade in trades:
            times.append(trade.trade_at.minute + trade.trade_at.hour * 60 -
                         day_start + 20)
            index.append(indexes[indicator](trade))

        self.scene.clear()
        try:
            max_index = max(index)
            min_index = min(index)
            if max_index == min_index:
                min_index = 0
            points = zip(times, map(lambda x:
                                    280-270*(x-min_index)/(max_index-min_index),
                                    index))

            path = QtGui.QPainterPath()
            path.moveTo(points[0][0], points[0][1])
            for p in points:
                path.lineTo(p[0], p[1])

            self.draw_time_axis()
            self.draw_value_axis(min_index, max_index)
            pathitem = self.scene.addPath(path)
            pathitem.setPen(QtGui.QPen(QtGui.QColor("red")))
        except:
            self.scene.addText("No data available")

    def draw_time_axis(self):
        self.scene.addLine(QtCore.QLineF(-50, 290, 700, 290))
        for i in range(20, 681, 60):
            self.scene.addLine(i, 280, i, 290)
            text = QtGui.QGraphicsTextItem("%02d:00" % (i/60 + 7))
            text.setPos(i-20, 295)
            self.scene.addItem(text)

    def draw_value_axis(self, minx, maxx):
        self.scene.addLine(QtCore.QLineF(20, -10, 20, 330))

        dx = (maxx - minx) / 9.0
        for i in range(280, 0, -30):
            self.scene.addLine(20, i, 30, i)
            text = QtGui.QGraphicsTextItem("%.0f" % (dx*(280-i)/30+minx))
            text.setPos(30, i-10)
            self.scene.addItem(text)


