from PyQt4.QtGui import QGraphicsScene


class PlotScene(QGraphicsScene):

    plotted = False

    def setStatusLabel(self, label):
        self.label = label

    def setPlotProps(self, padding, left, top, right, bottom):
        self.left = left + padding
        self.top = top + padding
        self.right = right - padding
        self.bottom = bottom - padding
        self.pixels = self.bottom - self.top

    def setScales(self, start, minx, maxx):
        self.start = start * 60
        self.minx = minx
        self.maxx = maxx
        self.dx = maxx - minx
        self.invert = maxx + minx

    def mouseMoveEvent(self, event):
        x, y = event.scenePos().x(), event.scenePos().y()
        if self.plotted and self.left < x < self.right and self.top < y < self.bottom:
            self.label.setText("approx. (%02d:%02d, %d)" % self.coords_transform(x, y))
        else:
            self.label.setText("")

    def coords_transform(self, x, y):
        xx = (self.start + x - self.left)
        yy = self.invert - (self.minx + self.dx * (y - self.top) / self.pixels)
        return divmod(xx, 60) +  (yy,)
