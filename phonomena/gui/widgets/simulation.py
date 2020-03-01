import common
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *


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
        self.layout.addWidget(self.description,1,0,2,1)
        self.layout.addWidget(self.test_button,0,1)
        self.layout.addWidget(self.test_result,1,1)
        self.layout.addWidget(self.run_button,2,1)
        self.layout.setColumnStretch(0, 2)
        self.layout.setColumnStretch(1, 1)
        self.layout.setHorizontalSpacing(80)
        margin = 30
        self.layout.setContentsMargins(margin,margin,margin,margin)

    def testButtonClick(self):
        try:
            common.solver.test()
            self.test_result.setText("PASSED")
            self.test_result.setStyleSheet("QLabel {background-color: green}")
        except Exception as e:
            msg = ": {}".format(e)
            self.test_result.setText("FAILED{}".format(msg))
            self.test_result.setStyleSheet("QLabel {background-color: red}")

    def runButtonClick(self):
        self.main_widget.runSimulation()

    def refresh(self):
        for c in common.solver_list:
            self.solvers.addItem(c.name)

    def importSolver(self):
        self.test_result.setText("")
        self.test_result.setStyleSheet("QLabel {background-color: none}")
        try:
            for s in common.solver_list:
                if s.name == self.solvers.currentText():
                    common.solver = s
                    self.description.setText(s.description)
                    break
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
        self.steps.setMaximum(50000)
        self.steps.valueChanged.connect(self.update)
        self.courant = QDoubleSpinBox()
        self.courant.setMinimum(0.1)
        self.courant.setMaximum(2)
        self.courant.setSingleStep(0.1)
        self.courant.valueChanged.connect(self.update)

        self.layout.addWidget(QLabel("Steps:"),0,0)
        self.layout.addWidget(self.steps,0,1)
        self.layout.addWidget(QLabel("Courant:"),1,0)
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
        common.cfg['simulation']['courant'] = self.courant.value()

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
        self.stress = QGridLayout()

        self.layout.addWidget(QLabel("<b>Material:</b>"),0,0)
        self.layout.addWidget(self.materials,0,1)
        self.layout.addWidget(QLabel("<b>Density:</b>"),1,0)
        self.layout.addWidget(self.density,1,1)
        self.layout.addWidget(QLabel("<b>Stress:</b>"),2,0,1,2)
        self.layout.addLayout(self.stress,3,0,1,2)

    def setMaterial(self):
        self.key = self.materials.currentText()
        properties = common.cfg['material']['properties'][self.key]
        self.density.setText("{:.2f}".format(properties['p']))
        stress = properties['c']

        for i in reversed(range(self.stress.count())):
            widgetToRemove = self.stress.itemAt(i).widget()
            self.stress.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

        for i in range(len(stress)):
            for j in range(len(stress[i])):
                txt = "{:.2f}".format(stress[i][j])
                self.stress.addWidget(QLabel(txt),i,j,alignment=QtCore.Qt.AlignCenter)

    def refresh(self):
        self.materials.clear()
        keys = common.cfg['material']['properties'].keys()
        self.materials.blockSignals(True)
        self.materials.addItems(keys)
        i = self.materials.findText(self.key)
        self.materials.setCurrentIndex(i)
        self.setMaterial() # Run manually
        self.materials.blockSignals(False)

class PrimaryMaterial(Material):
    def __init__(self, main_widget):
        super().__init__(main_widget)
        self.setTitle("Primary")
        self.key = common.cfg['material']['primary']


class SecondaryMaterial(Material):
    def __init__(self, main_widget):
        super().__init__(main_widget)
        self.setTitle("Secondary")
        self.key = common.cfg['material']['secondary']
