# boilerplate for package modules
if __name__ == '__main__':
    from pathlib import Path
    import sys
    file = Path(__file__).resolve()
    parent, root = file.parent, file.parents[1]
    sys.path.append(str(root))

    # Additionally remove the current file's directory from sys.path
    try:
        sys.path.remove(str(parent))
    except ValueError: # Already removed
        pass

import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import *

import common
from gui import widgets
from gui.worker import Worker

class Main(QWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window

        self.gui_update_pool = QtCore.QThreadPool()
        self.gui_update_pool.setExpiryTimeout(500)
        self.gui_update_pool.setMaxThreadCount(2)

        self.simpool = QtCore.QThreadPool()
        self.simpool.setMaxThreadCount(1)

        self.initUI()
        self.window.status_bar.showMessage("Ready.")

    def initUI(self):

        # Add mesh tab
        self.xy_mesh_view = widgets.mesh.XYGridView(self)
        self.yz_mesh_view = widgets.mesh.YZGridView(self)
        self.mesh_settings = widgets.mesh.Settings(self)

        # Mesh widget
        self.mesh = QWidget()
        mesh_tab_widget = QTabWidget()
        mesh_tab_widget.addTab(self.xy_mesh_view, "XY")
        mesh_tab_widget.addTab(self.yz_mesh_view, "YZ")
        mesh_layout = QHBoxLayout()
        mesh_layout.setSpacing(20)
        m = 20
        mesh_layout.setContentsMargins(m,m,m,m)
        mesh_layout.addWidget(self.mesh_settings, 1)
        mesh_layout.addWidget(mesh_tab_widget, 2)
        self.mesh.setLayout(mesh_layout)

        # Add simulation tab
        self.sim = QWidget()
        self.sim_settings = widgets.simulation.Settings(self)
        self.prim_material = widgets.simulation.PrimaryMaterial(self)
        self.sec_material = widgets.simulation.SecondaryMaterial(self)
        self.sim_solver = widgets.simulation.Solver(self)

        # Add results tab
        self.plot = QWidget()
        self.ux_plot = widgets.results.Plot(self)
        self.plot.setLayout(self.ux_plot)

        vlayout = QVBoxLayout()
        m = 20
        vlayout.setContentsMargins(m,m,m,m)
        hlayout = QHBoxLayout()
        hlayout.setSpacing(50)
        hlayout.addWidget(self.sim_settings, 1)
        hlayout.addWidget(self.prim_material, 1)
        hlayout.addWidget(self.sec_material, 1)
        vlayout.addLayout(hlayout, 2)
        vlayout.addWidget(self.sim_solver, 1)
        self.sim.setLayout(vlayout)

        main_tab_widget = QTabWidget()
        main_layout = QVBoxLayout()
        main_tab_widget.addTab(self.mesh, "Meshing")
        main_tab_widget.addTab(self.sim, "Simulation")
        main_tab_widget.addTab(self.plot, "Results")

        main_layout.addWidget(main_tab_widget)
        main_layout.addWidget(self.window.progress_bar)
        self.setLayout(main_layout)

    def drawResults(self):
        worker = Worker(self.ux_plot.refresh, callback_fns=self.window.callback_fns)
        self.gui_update_pool.start(worker)

    def buildMesh(self):
        def drawGrids():
            self.xy_mesh_view.drawGrid()
            self.yz_mesh_view.drawGrid()

        self.gui_update_pool.clear()
        worker = Worker(common.grid.buildMesh, callback_fns=self.window.callback_fns)
        worker.signals.finished.connect(drawGrids)
        self.gui_update_pool.start(worker)

    def runSimulation(self):
        time_steps = common.cfg['simulation']['steps']
        common.solver.init(
            grid = common.grid,
            material = common.material
        )
        worker = Worker(
            fn = common.solver.run,
            steps=time_steps,
            callback_fns=self.window.callback_fns
        )

        worker.signals.finished.connect(self.drawResults)
        self.simpool.start(worker)

    def refresh(self):
        self.mesh_settings.refresh()
        self.buildMesh()
        self.sim_settings.refresh()
        self.prim_material.refresh()
        self.sec_material.refresh()
        self.sim_solver.refresh()

    def closeEvent(self, event):
        if can_exit:
            event.accept() # let the window close
        else:
            event.ignore()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Phononema")
        self.resize(1100, 800)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.progress_bar = QProgressBar()

        self.callback_fns = {'status': self.updateStatus,
                             'error': self.showError,
                             'progress': self.updateProgress}

        self.main = Main(self)
        self.setCentralWidget(self.main)
        self.show()
        self.main.refresh()

    def showError(self, err):
        print(err)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(str(err[1]))
        msg.setInformativeText(str(err[2]))
        msg.setWindowTitle("Error")
        msg.exec_()

    def updateStatus(self, msg):
        assert type(msg) == str
        #print(msg)
        self.status_bar.showMessage(msg)

    def updateProgress(self, n):
        assert n >= 0 and n <= 100
        self.progress_bar.setValue(n)

    def open(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", QtCore.QDir.currentPath())
        if filename:
            common.importSettings(filename)
            common.init()
            self.main.refresh()

    def save(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", QtCore.QDir.currentPath())
        if filename:
            common.saveSettings(filename)

    def about(self):
        about = """<p>This program was developed for the ENPH 455 undergraduate thesis
        by Marc Cameron and extended by Matt Duke. It was designed to model acoustic wave
        transmission using the FDTD simulation.</p>"""
        QMessageBox.about(self, "Phonomena", about)

    def openRepo(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/matt-duke/phonomena'))

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.saveAct = QAction("&Save...", self, shortcut="Ctrl+S", triggered=self.save)
        self.exitAct = QAction("&Exit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.repoAct = QAction("&Repository", self, triggered=self.openRepo)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.repoAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.helpMenu)

def start():
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()
    sys.exit(0)

if __name__ == '__main__':
    common.importSettings()
    common.init()
    start()
