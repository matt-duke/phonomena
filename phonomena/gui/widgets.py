import common
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *

class MeshSettings(QGridLayout):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        self.x_width = QtWidgets.QDoubleSpinBox()
        self.y_width = QtWidgets.QDoubleSpinBox()
        self.z_width = QtWidgets.QDoubleSpinBox()
        self.max_dx = QtWidgets.QDoubleSpinBox()
        self.max_dy = QtWidgets.QDoubleSpinBox()
        self.min_d = QtWidgets.QDoubleSpinBox()
        self.slope = QtWidgets.QDoubleSpinBox()
        self.inclusions = QtWidgets.QTableWidget()
        self.inclusions.setColumnCount(3)
        self.inclusions.setHorizontalHeaderLabels(['X', 'Y', 'R'])
        self.inclusions.horizontalHeader().setStretchLastSection(True)
        self.inclusions.cellChanged.connect(self.meshButtonClick)

        self.x_width.valueChanged.connect(self.meshButtonClick)
        self.y_width.valueChanged.connect(self.meshButtonClick)
        self.max_dx.valueChanged.connect(self.meshButtonClick)
        self.max_dy.valueChanged.connect(self.meshButtonClick)
        self.slope.valueChanged.connect(self.meshButtonClick)
        self.min_d.valueChanged.connect(self.meshButtonClick)
        #self.inclusions.currentIndexChanged.connect()

        #self.mesh_button = QtWidgets.QPushButton('Mesh')
        #self.mesh_button.clicked.connect(self.meshButtonClick)

        self.addWidget(QLabel("X width:"),0,0)
        self.addWidget(self.x_width,0,1)
        self.addWidget(QLabel("Y width:"),1,0)
        self.addWidget(self.y_width,1,1)
        self.addWidget(QLabel("Z width:"),2,0)
        self.addWidget(self.z_width,2,1)
        self.addWidget(QLabel("Max X spacing:"),3,0)
        self.addWidget(self.max_dx,3,1)
        self.addWidget(QLabel("Max Y spacing:"),4,0)
        self.addWidget(self.max_dy,4,1)
        self.addWidget(QLabel("Min spacing:"),5,0)
        self.addWidget(self.min_d,5,1)
        self.addWidget(QLabel("Slope:"),6,0)
        self.addWidget(self.slope,6,1)
        self.addWidget(QLabel("Inclusions:"),7,0,1,2)
        self.addWidget(self.inclusions,8,0,1,2)
        #self.addWidget(self.mesh_button,7,1)

    def blockEvents(self, bool):
        self.x_width.blockSignals(bool)
        self.y_width.blockSignals(bool)
        self.max_dx.blockSignals(bool)
        self.max_dy.blockSignals(bool)
        self.slope.blockSignals(bool)
        self.min_d.blockSignals(bool)
        self.inclusions.blockSignals(bool)

    def refresh(self):
        self.blockEvents(True)
        self.x_width.setValue(common.mesh.size_x)
        self.y_width.setValue(common.mesh.size_y)
        self.z_width.setValue(common.mesh.size_z)
        self.max_dx.setValue(common.mesh.default_dx)
        self.max_dy.setValue(common.mesh.default_dy)
        self.min_d.setValue(common.mesh.min_d)
        self.min_d.setMinimum(0.1)
        self.min_d.setMaximum(min((self.max_dx.value(),self.max_dy.value())))
        self.slope.setSingleStep(0.1)
        self.slope.setValue(common.mesh.slope)
        self.slope.setMinimum(0.1)
        self.slope.setMaximum(1)
        self.slope.setSingleStep(0.1)

        self.inclusions.clearSpans()
        num_rows = len(common.mesh.targets)
        for i in range(num_rows):
            self.inclusions.insertRow(i)
            x = QtWidgets.QTableWidgetItem(str(common.mesh.targets[i]['x']))
            y = QtWidgets.QTableWidgetItem(str(common.mesh.targets[i]['y']))
            r = QtWidgets.QTableWidgetItem(str(common.mesh.targets[i]['r']))
            self.inclusions.setItem(i, 0, x)
            self.inclusions.setItem(i, 1, y)
            self.inclusions.setItem(i, 2, r)
        self.blockEvents(False)

    def updateMesh(self):
        common.mesh.size_x = self.x_width.value()
        common.mesh.size_y = self.y_width.value()
        common.mesh.size_z = self.z_width.value()
        common.mesh.default_dx = self.max_dx.value()
        common.mesh.default_dy = self.max_dy.value()
        common.mesh.min_d = self.min_d.value()
        common.mesh.slope = self.slope.value()

        common.mesh.clearInclusions()
        num_rows = self.inclusions.rowCount()
        if num_rows > 0:
            for i in range(num_rows):
                x = self.inclusions.item(i, 0).text()
                y = self.inclusions.item(i, 1).text()
                r = self.inclusions.item(i, 2).text()
                common.mesh.addInclusion(x,y,r)

    def meshButtonClick(self):
        self.updateMesh()
        self.main_window.buildMesh()

class Grid(QtWidgets.QGraphicsScene):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.lines = []
        self.scale = 20
        self.min_scale = 10
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
        self.deleteGrid()
        if len(common.mesh.x) * len(common.mesh.y) == 0:
            return

        arr_x = common.mesh.x * self.scale
        width = arr_x[-1]
        arr_y = common.mesh.y * self.scale
        height = arr_y[-1]

        self.setSceneRect(0, 0, width, height)
        self.setItemIndexMethod(QtWidgets.QGraphicsScene.NoIndex)

        pen = QtGui.QPen(QtGui.QColor(0,0,0), 1, QtCore.Qt.SolidLine)

        for x in arr_x:
            self.lines.append(self.addLine(x,0,x,height,pen))

        for y in arr_y:
            self.lines.append(self.addLine(0,y,width,y,pen))

    def setVisible(self,visible=True):
        for line in self.lines:
            line.setVisible(visible)

    def deleteGrid(self):
        for line in self.lines:
            self.removeItem(line)
        del self.lines[:]

    def setOpacity(self,opacity):
        for line in self.lines:
            line.setOpacity(opacity)
