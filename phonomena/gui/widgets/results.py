import common
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *

import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure


class Plot(QGridLayout):
    def __init__(self, main_widget):
        super().__init__()

        self.main_widget = main_widget
        self.canvas = FigureCanvas(Figure())
        self.ax = self.canvas.figure.subplots()
        self.addWidget(self.canvas)

    def refresh(self, *args, **kwargs):
        uz = common.grid.uz[:,:,0]
        self.ax.clear()
        X,Y = np.meshgrid(common.grid.y, common.grid.x)
        self.ax.contourf(X,Y,uz)
        self.ax.figure.canvas.draw()
