#https://gist.github.com/acbetter/32c575803ec361c3e82064e60db4e3e0
#https://kushaldas.in/posts/pyqt5-thread-example.html

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

        self.meshpool = QtCore.QThreadPool()
        self.meshpool.setExpiryTimeout(5000)
        self.meshpool.setMaxThreadCount(1)

        self.initUI()
        self.window.status_bar.showMessage("Ready.")

    def initUI(self):
        # Widgets
        self.mesh_widget = widgets.Grid(self)
        self.mesh_view = QGraphicsView()
        self.mesh_view.setScene(self.mesh_widget)

        self.settings = QGroupBox("Settings")
        self.mesh_settings = widgets.MeshSettings(self)

        self.run_button = QPushButton()

        # Layouts
        self.vlayout = QVBoxLayout()
        self.hLayout = QHBoxLayout()
        bottomHLayout = QHBoxLayout()
        self.setLayout(self.vlayout)
        self.settings.setLayout(self.mesh_settings)

        label1 = QLabel("Widget in Tab 1.")

        tabwidget = QTabWidget()
        tabwidget.addTab(self.mesh_view, "Mesh")
        tabwidget.addTab(label1, "Simulation")
        tabwidget.addTab(label1, "Spectrum")
        self.hLayout.addWidget(self.settings, 1)
        self.hLayout.addWidget(tabwidget, 2)
        self.vlayout.addLayout(self.hLayout)
        self.vlayout.addLayout(bottomHLayout)

    def buildMesh(self):
         self.meshpool.clear()
         worker = Worker(common.mesh.buildMesh, callback_fns=self.window.callback_fns)
         worker.signals.finished.connect(self.mesh_widget.drawGrid)
         self.meshpool.start(worker)

    def refresh(self):
        self.mesh_settings.refresh()
        self.buildMesh()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Used to force quit all running threads
        #quit_action = QAction("Quit", self)
        #quit_action.triggered.connect(quit)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Phononema")
        self.resize(900, 700)

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
            print(common.mesh.size_x)
            common.import_settings(filename)
            common.init()
            self.main.refresh()

    def save(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", QtCore.QDir.currentPath())
        if filename:
            common.save_settings(filename)

    def about(self):
        QMessageBox.about(self, "Phonomena",
                          "<p>This program was developed for the ENPH 455 "
                          "undergraduate thesis by Marc Cameron and extended "
                          "by Matt Duke. It was designed to model acoustic "
                          "wave transmission using the FDTD simulation.</p>")

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.saveAct = QAction("&Save...", self, shortcut="Ctrl+S", triggered=self.save)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.aboutAct = QAction("&About", self, triggered=self.about)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.helpMenu)

def start():
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()
    sys.exit(0)

if __name__ == '__main__':
    common.import_settings()
    common.init()
    start()
