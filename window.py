from PyQt4 import QtCore, QtGui


class MainWindow(QtGui.QDialog):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.create_layout()

    def create_layout(self):
        trade_label = QtGui.QLabel("Trade code:")
        self.trade_combo = QtGui.QComboBox()
        trade_label.setBuddy(self.trade_combo)

        date_label = QtGui.QLabel("Date:")
        self.date_picker = QtGui.QDateEdit()
        self.date_picker.setDisplayFormat("MMM d, yyyy")
        self.date_picker.setDate(QtCore.QDate.currentDate())
        date_label.setBuddy(self.date_picker)

        self.fetch_button = QtGui.QPushButton("Start fetching")
        self.stop_button = QtGui.QPushButton("Stop fetching")

        self.canvas = QtGui.QGraphicsView()
        self.status = QtGui.QLabel("Ready")

        ind_label = QtGui.QLabel("Indicator:")
        self.ind_combo = QtGui.QComboBox()
        ind_label.setBuddy(self.ind_combo)

        hbox_trade = QtGui.QHBoxLayout()
        hbox_trade.addWidget(trade_label)
        hbox_trade.addWidget(self.trade_combo)

        hbox_date = QtGui.QHBoxLayout()
        hbox_date.addWidget(date_label)
        hbox_date.addWidget(self.date_picker)

        hbox_ind = QtGui.QHBoxLayout()
        hbox_ind.addWidget(ind_label)
        hbox_ind.addWidget(self.ind_combo)
        hbox_ind.addStretch()

        hbox_buttons = QtGui.QHBoxLayout()
        hbox_buttons.addWidget(self.fetch_button)
        hbox_buttons.addWidget(self.stop_button)

        grid = QtGui.QGridLayout(self)
        grid.addLayout(hbox_trade, 0, 0)
        grid.addLayout(hbox_date, 0, 1)
        grid.addLayout(hbox_ind, 0, 2)
        grid.addLayout(hbox_buttons, 0, 3)
        grid.addWidget(self.canvas, 1, 0, 1, 4)
        grid.addWidget(self.status, 2, 0, 1, 4)

