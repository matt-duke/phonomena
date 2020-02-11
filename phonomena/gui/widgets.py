import common
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *


class InclusionTable(QtWidgets.QTableWidget):
    def __init__(self):
        super().__init__()

        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['X', 'Y', 'R'])
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

    def blankRow(self):
        self.blockSignals(True)
        self.addItem(common.mesh.size_x/2, common.mesh.size_y/2,1)
        self.blockSignals(False)
        #self.cellChanged.emit(0,0)

    def addItem(self,x,y,r):
        i = self.rowCount()
        self.insertRow(i)

        nums = (x,y,r)
        for j in range(len(nums)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, float(nums[j]))
            self.setItem(i, j, item)

    def getRow(self, i):
        x = self.item(i, 0).text()
        y = self.item(i, 1).text()
        r = self.item(i, 2).text()
        return x,y,r

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
        self.inclusions = InclusionTable()
        #self.inclusions.clicked.connect(self.addInclusion)

        self.x_width.valueChanged.connect(self.meshButtonClick)
        self.y_width.valueChanged.connect(self.meshButtonClick)
        self.max_dx.valueChanged.connect(self.meshButtonClick)
        self.max_dy.valueChanged.connect(self.meshButtonClick)
        self.slope.valueChanged.connect(self.meshButtonClick)
        self.min_d.valueChanged.connect(self.meshButtonClick)
        self.inclusions.cellChanged.connect(self.meshButtonClick)

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
        self.addWidget(QLabel("Inclusion regions:"),7,0,1,2)
        self.addWidget(self.inclusions,8,0,1,2)

        self.setVerticalSpacing(25)
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
        self.max_dx.setValue(common.mesh.max_dx)
        self.max_dy.setValue(common.mesh.max_dy)
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
            t = common.mesh.targets[i]
            self.inclusions.addItem(t['x'],t['y'],t['r'])
        self.blockEvents(False)

    def updateMesh(self):
        common.mesh.size_x = self.x_width.value()
        common.mesh.size_y = self.y_width.value()
        common.mesh.size_z = self.z_width.value()
        common.mesh.max_dx = self.max_dx.value()
        common.mesh.max_dy = self.max_dy.value()
        common.mesh.min_d = self.min_d.value()
        common.mesh.slope = self.slope.value()

        common.mesh.clearInclusions()
        num_rows = self.inclusions.rowCount()
        for i in range(num_rows):
            x,y,r = self.inclusions.getRow(i)
            common.mesh.addInclusion(x,y,r)

    def meshButtonClick(self):
        self.updateMesh()
        self.main_window.buildMesh()

class Grid(QtWidgets.QGraphicsScene):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.obj = []
        self.circles = []
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
            self.obj.append(self.addLine(x,0,x,height,pen))

        for y in arr_y:
            self.obj.append(self.addLine(0,y,width,y,pen))

        pen = QtGui.QPen(QtGui.QColor(255,0,0), 2, QtCore.Qt.SolidLine)
        for t in common.mesh.targets:
            x = (t['x']-t['r'])*self.scale
            y = (t['y']-t['r'])*self.scale
            d = 2*t['r']*self.scale
            self.obj.append(self.addEllipse(x, y, d, d, pen))

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
