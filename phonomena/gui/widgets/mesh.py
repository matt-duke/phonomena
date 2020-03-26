import common
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
import numpy as np


class InclusionTable(QtWidgets.QTableWidget):
    def __init__(self):
        super().__init__()

        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['X', 'Y', 'Z', 'R'])
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        addAction = QtWidgets.QAction("Add..", self)
        removeAction = QtWidgets.QAction("Remove..", self)
        addAction.triggered.connect(self.blankRow)
        removeAction.triggered.connect(self.removeCurrentRow)
        self.addAction(addAction)
        self.addAction(removeAction)

    def removeCurrentRow(self):
        i = self.currentRow()
        self.removeRow(i)
        self.cellChanged.emit(0,0)

    def blankRow(self):
        self.blockSignals(True)
        self.addItem(1,1,1,1)
        self.blockSignals(False)

    def addItem(self,x,y,z,r):
        i = self.rowCount()
        self.insertRow(i)
        self.cellChanged.emit(0,0)

        nums = (x,y,z,r)
        for j in range(len(nums)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, float(nums[j]))
            self.setItem(i, j, item)

    def getRow(self, i):
        x = self.item(i, 0).text()
        y = self.item(i, 1).text()
        z = self.item(i, 2).text()
        r = self.item(i, 3).text()
        return x,y,z,r

class Settings(QGroupBox):
    def __init__(self, main_widget):
        super().__init__()
        self.setTitle("Settings")
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.main_widget = main_widget

        self.x_width = QtWidgets.QSpinBox()
        self.y_width = QtWidgets.QSpinBox()
        self.z_width = QtWidgets.QSpinBox()
        self.max_dx = QtWidgets.QDoubleSpinBox()
        self.max_dy = QtWidgets.QDoubleSpinBox()
        self.max_dz = QtWidgets.QDoubleSpinBox()
        self.min_d = QtWidgets.QDoubleSpinBox()
        self.slope = QtWidgets.QDoubleSpinBox()
        self.inclusions = InclusionTable()

        self.x_width.valueChanged.connect(self.meshButtonClick)
        self.y_width.valueChanged.connect(self.meshButtonClick)
        self.z_width.valueChanged.connect(self.meshButtonClick)
        self.max_dx.valueChanged.connect(self.meshButtonClick)
        self.max_dy.valueChanged.connect(self.meshButtonClick)
        self.max_dz.valueChanged.connect(self.meshButtonClick)
        self.min_d.valueChanged.connect(self.meshButtonClick)
        self.slope.valueChanged.connect(self.meshButtonClick)
        self.inclusions.cellChanged.connect(self.meshButtonClick)

        self.layout.addWidget(QLabel("X width:"),0,0)
        self.layout.addWidget(self.x_width,0,1)
        self.layout.addWidget(QLabel("Y width:"),1,0)
        self.layout.addWidget(self.y_width,1,1)
        self.layout.addWidget(QLabel("Z width:"),2,0)
        self.layout.addWidget(self.z_width,2,1)
        self.layout.addWidget(QLabel("Max X spacing:"),3,0)
        self.layout.addWidget(self.max_dx,3,1)
        self.layout.addWidget(QLabel("Max Y spacing:"),4,0)
        self.layout.addWidget(self.max_dy,4,1)
        self.layout.addWidget(QLabel("Max Z spacing:"),5,0)
        self.layout.addWidget(self.max_dz,5,1)
        self.layout.addWidget(QLabel("Min spacing:"),6,0)
        self.layout.addWidget(self.min_d,6,1)
        self.layout.addWidget(QLabel("Slope:"),7,0)
        self.layout.addWidget(self.slope,7,1)
        self.layout.addWidget(QLabel("Inclusion regions:"),8,0,1,2)
        self.layout.addWidget(self.inclusions,9,0,1,2)

        self.layout.setVerticalSpacing(25)
        #self.addWidget(self.mesh_button,7,1)

    def blockSignals(self, bool):
        self.x_width.blockSignals(bool)
        self.y_width.blockSignals(bool)
        self.z_width.blockSignals(bool)
        self.max_dx.blockSignals(bool)
        self.max_dy.blockSignals(bool)
        self.max_dz.blockSignals(bool)
        self.slope.blockSignals(bool)
        self.min_d.blockSignals(bool)
        self.inclusions.blockSignals(bool)

    def refresh(self):
        self.blockSignals(True)
        self.x_width.setValue(common.grid.size_x)
        self.x_width.setMinimum(1)
        self.x_width.setMaximum(10000)
        self.y_width.setValue(common.grid.size_y)
        self.y_width.setMinimum(1)
        self.y_width.setMaximum(10000)
        self.z_width.setValue(common.grid.size_z)
        self.z_width.setMinimum(1)
        self.z_width.setMaximum(10000)
        self.max_dx.setValue(common.grid.max_dx)
        self.max_dx.setMinimum(common.grid.min_d)
        self.max_dy.setValue(common.grid.max_dy)
        self.max_dy.setMinimum(common.grid.min_d)
        self.max_dz.setValue(common.grid.max_dz)
        self.max_dz.setMinimum(common.grid.min_d)
        self.min_d.setValue(common.grid.min_d)
        self.min_d.setMinimum(0.1)
        self.min_d.setMaximum(min((self.max_dx.value(),self.max_dy.value())))
        self.slope.setSingleStep(0.1)
        self.slope.setValue(common.grid.slope)
        self.slope.setMinimum(0.1)
        self.slope.setMaximum(1)
        self.slope.setSingleStep(0.1)

        self.inclusions.clearSpans()
        num_rows = len(common.grid.targets)
        for i in range(num_rows):
            t = common.grid.targets[i]
            self.inclusions.addItem(t['x'],t['y'],t['z'],t['r'])

        self.blockSignals(False)

    def update(self):
        common.grid.size_x = self.x_width.value()
        common.grid.size_y = self.y_width.value()
        common.grid.size_z = self.z_width.value()
        common.grid.max_dx = self.max_dx.value()
        common.grid.max_dy = self.max_dy.value()
        common.grid.max_dz = self.max_dz.value()
        common.grid.min_d = self.min_d.value()
        common.grid.slope = self.slope.value()

        common.grid.clearInclusions()
        num_rows = self.inclusions.rowCount()
        for i in range(num_rows):
            x,y,z,r = self.inclusions.getRow(i)
            common.grid.addInclusion(x=x,y=y,z=z,r=r)

    def meshButtonClick(self):
        self.update()
        self.main_widget.buildMesh()


class GridClass(QtWidgets.QGraphicsScene):
    def __init__(self, main_widget):
        super().__init__()

        self.main_widget = main_widget
        self.obj = []
        self.circles = []
        self.scale = 10
        self.min_scale = 5
        self.max_scale = 50

        self.setOpacity(1)

    def wheelEvent(self, event):
        prev_scale = self.scale
        self.scale += event.delta()/120
        self.scale = self.max_scale if self.scale > self.max_scale else self.scale
        self.scale = self.min_scale if self.scale < self.min_scale else self.scale
        if self.scale != prev_scale:
            self.drawGrid()

    def drawGrid(self):
        # REPLACE FUNCTION
        pass

    def setVisible(self,visible=True):
        for line in self.obj:
            line.setVisible(visible)

    def deleteGrid(self):
        for line in self.obj:
            self.removeItem(line)
        del self.obj[:]

    def setOpacity(self,opacity):
        for line in self.obj:
            line.setOpacity(opacity)


class XYGridView(QtWidgets.QGraphicsView):
    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self.grid = self.Grid(self.main_widget)
        self.setRenderHints(QtGui.QPainter.Antialiasing)
        self.setScene(self.grid)

    def drawGrid(self):
        self.grid.drawGrid()

    class Grid(GridClass):
        def drawGrid(self):
            self.deleteGrid()
            if len(common.grid.x) * len(common.grid.y) == 0:
                return

            arr_x = common.grid.x * self.scale
            width = arr_x[-1]
            arr_y = common.grid.y * self.scale
            height = arr_y[-1]

            self.setSceneRect(0, 0, width, height)
            self.setItemIndexMethod(QtWidgets.QGraphicsScene.NoIndex)

            pen = QtGui.QPen(QtGui.QColor(0,0,0), 1, QtCore.Qt.SolidLine)

            for x in arr_x:
                self.obj.append(self.addLine(x,0,x,height,pen))

            for y in arr_y:
                self.obj.append(self.addLine(0,y,width,y,pen))

            pen = QtGui.QPen(QtGui.QColor(255,0,0), 2, QtCore.Qt.SolidLine)
            for t in common.grid.targets:
                x = (t['x']-t['r'])*self.scale
                y = (t['y']-t['r'])*self.scale
                d = 2*t['r']*self.scale
                self.obj.append(self.addEllipse(x, y, d, d, pen))

class YZGridView(QtWidgets.QGraphicsView):
    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self.grid = self.Grid(self.main_widget)
        self.setRenderHints(QtGui.QPainter.Antialiasing)
        self.setScene(self.grid)

    def drawGrid(self):
        self.grid.drawGrid()

    class Grid(GridClass):

        def drawGrid(self):
            self.deleteGrid()

            if len(common.grid.y) * common.grid.size_z == 0:
                return

            arr_y = common.grid.y * self.scale
            width = arr_y[-1]
            arr_z = common.grid.z * self.scale
            height = arr_z[-1]

            self.setSceneRect(0, 0, width, height)
            self.setItemIndexMethod(QtWidgets.QGraphicsScene.NoIndex)

            pen = QtGui.QPen(QtGui.QColor(0,0,0), 1, QtCore.Qt.SolidLine)

            for y in arr_y:
                self.obj.append(self.addLine(y,0,y,height,pen))

            for z in arr_z:
                self.obj.append(self.addLine(0,z,width,z,pen))

            pen = QtGui.QPen(QtGui.QColor(255,0,0), 2, QtCore.Qt.SolidLine)
            for t in common.grid.targets:
                z = (t['z']-t['r'])*self.scale
                y = (t['y']-t['r'])*self.scale
                d = 2*t['r']*self.scale
                self.obj.append(self.addLine(y, 0, y, z, pen))
                self.obj.append(self.addLine(y+d, 0, y+d, z, pen))
                self.obj.append(self.addLine(y, z, y+d, z, pen))
