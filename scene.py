# scene.py
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
