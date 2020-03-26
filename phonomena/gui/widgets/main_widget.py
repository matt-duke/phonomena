from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import *
from gui.worker import Worker

from . import mesh, simulation, analysis, log
import common

import logging
logger = logging.getLogger(__name__)

class Main(QWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window

        self.log_handler = log.QPlainTextEditLogger(self)
        logging.getLogger().addHandler(self.log_handler)

        self.gui_update_pool = QtCore.QThreadPool()
        self.gui_update_pool.setExpiryTimeout(500)
        self.gui_update_pool.setMaxThreadCount(2)

        self.simpool = QtCore.QThreadPool()
        self.simpool.setMaxThreadCount(1)

        self.initUI()
        self.window.status_bar.showMessage("Ready.")

    def initUI(self):

        # Add mesh tab
        self.xy_mesh_view = mesh.XYGridView(self)
        self.yz_mesh_view = mesh.YZGridView(self)
        self.mesh_settings = mesh.Settings(self)

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
        self.sim_settings = simulation.Settings(self)
        self.prim_material = simulation.PrimaryMaterial(self)
        self.sec_material = simulation.SecondaryMaterial(self)
        self.sim_solver = simulation.Solver(self)

        # Add results tab
        self.analysis = analysis.Viewer(self)

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
        main_tab_widget.addTab(self.analysis, "Analysis")
        main_tab_widget.addTab(self.log_handler.widget, "Log")

        main_layout.addWidget(main_tab_widget)
        main_layout.addWidget(self.window.progress_bar)
        self.setLayout(main_layout)

    def drawResults(self):
        self.analysis.loadHDF(common.solver.file)
        self.analysis.refresh()

    def buildMesh(self):
        def drawGrids():
            self.xy_mesh_view.drawGrid()
            self.yz_mesh_view.drawGrid()
            self.analysis.refresh()

        def build(*args, **kwargs):
            signals = kwargs['signals']
            common.grid.buildMesh(args, kwargs)
            common.grid.update()
            common.material.update()

        self.gui_update_pool.clear()
        worker = Worker(build, callback_fns=self.window.callback_fns)
        worker.signals.finished.connect(drawGrids)
        self.gui_update_pool.start(worker)

    def runSimulation(self):

        if self.simpool.activeThreadCount() > 0:
            self.cancelSimulation()
            return

        time_steps = common.cfg['simulation']['steps']
        common.solver.init(
            grid = common.grid,
            material = common.material,
            steps = time_steps
        )
        worker = Worker(
            fn = common.solver.run,
            callback_fns=self.window.callback_fns
        )

        worker.signals.finished.connect(self.drawResults)
        logger.info("Starting simulation...")
        self.simpool.start(worker)

    def cancelSimulation(self):
        if self.simpool.activeThreadCount() > 0:
            logger.warning("Cancelling simulation...")
            common.solver.running.clear()
            self.simpool.waitForDone(msecs=1000)
        self.window.updateProgress(0)

    def refresh(self):
        self.mesh_settings.refresh()
        self.buildMesh()
        self.sim_settings.refresh()
        self.prim_material.refresh()
        self.sec_material.refresh()
        self.sim_solver.refresh()
