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

import logging
logger = logging.getLogger(__name__)

# Restore PyQt5 debug behaviour (print exception) https://stackoverflow.com/questions/33736819/pyqt-no-error-msg-traceback-on-exit
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

sys.excepthook = except_hook

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

        self.main = widgets.main_widget.Main(self)
        self.setCentralWidget(self.main)
        self.show()
        self.main.refresh()

    def closeEvent(self, event):
        self.main.cancelSimulation()
        if True:
            common.setTempdir() # clear HDF files on exit
            event.accept()
        else:
            event.ignore()

    def showError(self, err):
        logger.error(err)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(str(err[0]))
        msg.setInformativeText(str(err[1]))
        msg.setWindowTitle("Error")
        msg.exec_()

    def updateStatus(self, msg):
        assert type(msg) == str
        #print(msg)
        self.status_bar.showMessage(msg)
        logger.debug("received status: {}".format(msg))

    def updateProgress(self, n):
        assert n >= 0 and n <= 100 and type(n) == int
        self.progress_bar.setValue(n)

    def open(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", QtCore.QDir.currentPath(), ("JSON (*.json)"))
        if filename:
            try:
                common.loadSettings(filename)
                self.main.refresh()
            except Exception as e:
                self.showError(e)

    def save(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", QtCore.QDir.currentPath(), ("JSON (*.json)"))
        if filename:
            common.saveSettings(filename)

    def about(self):
        about = """<p>This program was developed for the ENPH 455 undergraduate thesis
        by Marc Cameron and extended by Matt Duke. It was designed to model acoustic wave
        transmission using the FDTD simulation.
        <br><br>Version: {}<br>Build: {}</p>""".format(common.info.version, common.info.build)
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
