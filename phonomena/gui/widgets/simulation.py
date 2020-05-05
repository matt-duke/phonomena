import common
import json
import logging
import time
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *

logger = logging.getLogger(__name__)


class Solver(QGroupBox):
    def __init__(self, main_widget):
        super().__init__()

        self.layout = QGridLayout()
        self.main_widget = main_widget
        self.setLayout(self.layout)

        self.setTitle("Solver")

        self.solvers = QComboBox()
        self.solvers.currentIndexChanged.connect(self.importSolver)
        self.lbl = QLabel()
        self.description = QTextEdit()
        self.cfg_str = QLineEdit()
        self.cfg_str.editingFinished.connect(self.updateSettingsString)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.lbl)
        hlayout.addWidget(self.solvers)
        self.test_button = QPushButton()
        self.test_button.setText("Test solver")
        self.test_button.clicked.connect(self.testButtonClick)
        self.test_result = QLabel()
        self.run_button = QPushButton()
        self.run_button.setText("Run simulation")
        self.run_button.clicked.connect(self.runButtonClick)
        self.layout.addLayout(hlayout,0,0)
        self.layout.addWidget(self.description,1,0,3,1)
        self.layout.addWidget(self.test_button,0,1)
        self.layout.addWidget(self.test_result,1,1)
        self.layout.addWidget(self.cfg_str,2,1)
        self.layout.addWidget(self.run_button,3,1)
        self.layout.setColumnStretch(0, 2)
        self.layout.setColumnStretch(1, 1)
        self.layout.setHorizontalSpacing(80)
        self.layout.setVerticalSpacing(10)
        margin = 30
        self.layout.setContentsMargins(margin,margin,margin,margin)

    def testButtonClick(self):
        try:
            self.test_result.setText("Testing...")
            self.test_result.setStyleSheet("QLabel {background-color: white}")
            self.main_widget.delay(1000)
            common.solver.test()
            self.test_result.setText("PASSED")
            self.test_result.setStyleSheet("QLabel {background-color: green}")
        except Exception as e:
            msg = ": {}".format(e)
            self.test_result.setText("FAILED{}".format(msg))
            self.test_result.setStyleSheet("QLabel {background-color: red}")

    def updateSettingsString(self):
        txt = self.cfg_str.text()
        try:
            cfg = json.loads(txt)
            common.solver.cfg = cfg
            logger.info("{} cfg changed to {}".format(common.solver.name, common.solver.cfg))
        except json.JSONDecodeError as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(str(e))
            msg.setWindowTitle("Error")
            msg.exec_()

    def runButtonClick(self):
        self.main_widget.runSimulation()

    def refresh(self):
        self.solvers.clear()
        for k in common.solver_dict.keys():
            self.solvers.addItem(k)

    def importSolver(self):
        self.test_result.setText("NOT TESTED")
        self.test_result.setStyleSheet("QLabel {background-color: none}")
        try:
            assert self.solvers.currentText() in common.solver_dict.keys()
            common.solver = common.solver_dict[self.solvers.currentText()]
            self.description.setText(common.solver.description)
            self.cfg_str.setText(json.dumps(common.solver.cfg))
            self.lbl.setText("<p>&#10004;</p>") # check mark

        except Exception as e:
            self.lbl.setText("<p><b>X</b></p>") # X mark
            self.description.setText(str(e))


class Settings(QGroupBox):
    def __init__(self, main_widget):
        super().__init__()

        self.layout = QGridLayout()
        self.main_widget = main_widget
        self.setLayout(self.layout)

        self.setTitle("Settings")

        self.steps = QSpinBox()
        self.steps.setMinimum(1)
        self.steps.setMaximum(100000)
        self.steps.editingFinished.connect(self.update)
        self.steps.setMinimumWidth(10)
        self.courant = QDoubleSpinBox()
        self.courant.setMinimum(0.001)
        self.courant.setMaximum(2)
        self.courant.setSingleStep(0.1)
        self.courant.setMinimumWidth(10)
        self.courant.editingFinished.connect(self.update)

        self.layout.addWidget(QLabel("Number of time steps:"),0,0)
        self.layout.addWidget(self.steps,0,1)
        self.layout.addWidget(QLabel("CFL (Courant) condition:"),1,0)
        self.layout.addWidget(self.courant,1,1)
        margin = 20
        self.layout.setContentsMargins(margin,margin,margin,margin)

    def blockSignals(self, bool):
        self.steps.blockSignals(bool)
        self.courant.blockSignals(bool)

    def refresh(self):
        self.blockSignals(True)
        self.steps.setValue(common.cfg['simulation']['steps'])
        self.courant.setValue(common.cfg['simulation']['courant'])
        self.blockSignals(False)

    def update(self):
        common.cfg['simulation']['steps'] = self.steps.value()
        common.material.c_max = self.courant.value()

class Material(QGroupBox):
    def __init__(self, main_widget):
        super().__init__()

        self.layout = QGridLayout()
        self.main_widget = main_widget
        self.setLayout(self.layout)

        self.key = ""

        self.materials = QComboBox()
        self.materials.currentIndexChanged.connect(self.setMaterial)

        self.density = QLabel()
        self.elasticity = QGridLayout()

        self.layout.addWidget(QLabel("Material:"),0,0)
        self.layout.addWidget(self.materials,0,1)
        self.layout.addWidget(QLabel("Density [kg/m<sup>3</sup>]:"),1,0)
        self.layout.addWidget(self.density,1,1)
        self.layout.addWidget(QLabel("Elasticity [Pa x1<sup>10</sup>]:"),2,0,1,2)
        self.layout.addLayout(self.elasticity,3,0,1,2)

    def setMaterial(self):
        self.key = self.materials.currentText()
        assert self.key in common.material.properties.keys()
        properties = common.material.properties[self.key]
        self.density.setText("{:.2f}".format(properties['p']))
        stress = properties['c']

        for i in reversed(range(self.elasticity.count())):
            widgetToRemove = self.elasticity.itemAt(i).widget()
            self.elasticity.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

        for i in range(len(stress)):
            for j in range(len(stress[i])):
                txt = "{:.2f}".format(stress[i][j]*1e-10)
                self.elasticity.addWidget(QLabel(txt),i,j,alignment=QtCore.Qt.AlignCenter)

    def refresh(self):
        self.materials.blockSignals(True)
        self.materials.clear()
        keys = common.cfg['material']['properties'].keys()
        assert self.key in keys
        self.materials.addItems(keys)
        i = self.materials.findText(self.key)
        self.materials.setCurrentIndex(i)
        self.setMaterial()
        self.materials.blockSignals(False)

class PrimaryMaterial(Material):
    def __init__(self, main_widget):
        super().__init__(main_widget)
        self.setTitle("Primary")

    def setMaterial(self):
        super().setMaterial()
        common.material.setPrimary(self.key)

    def refresh(self):
        self.key = common.cfg['material']['primary']
        super().refresh()

class SecondaryMaterial(Material):
    def __init__(self, main_widget):
        super().__init__(main_widget)
        self.setTitle("Secondary")

    def setMaterial(self):
        super().setMaterial()
        common.material.setSecondary(self.key)

    def refresh(self):
        self.key = common.cfg['material']['secondary']
        super().refresh()
