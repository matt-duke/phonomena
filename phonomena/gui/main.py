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

class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Widgets
        self.mesh = widgets.Grid(self)
        self.meshView = QGraphicsView()
        self.meshView.setScene(self.mesh)

        self.progress = QProgressBar()

        self.mesh_button = QtWidgets.QPushButton('Mesh', self)
        self.mesh_button.clicked.connect(self.meshButtonClick)

        groupbox = QGroupBox("Settings")

        # Layouts
        self.vlayout = QVBoxLayout()
        self.hLayout = QHBoxLayout()
        self.setLayout(self.vlayout)
        self.sg_layout = QGridLayout()
        self.sg_layout.addWidget(QLabel("X width:"),0,0)
        self.sg_layout.addWidget(QLineEdit(),0,1)
        self.sg_layout.addWidget(QLabel("Y width:"),1,0)
        self.sg_layout.addWidget(QLineEdit(),1,1)
        self.sg_layout.addWidget(QLabel("Z width:"),2,0)
        self.sg_layout.addWidget(QLineEdit(),2,1)
        self.sg_layout.addWidget(QLabel("Max spacing:"),3,0)
        self.sg_layout.addWidget(QLineEdit(),3,1)
        self.sg_layout.addWidget(QLabel("Min spacing:"),4,0)
        self.sg_layout.addWidget(QLineEdit(),4,1)
        self.sg_layout.addWidget(QLabel("Slope:"),5,0)
        self.sg_layout.addWidget(QLineEdit(),5,1)
        self.sg_layout.addWidget(self.mesh_button,6,0)
        groupbox.setLayout(self.sg_layout)

        label1 = QLabel("Widget in Tab 1.")

        tabwidget = QTabWidget()
        tabwidget.addTab(self.meshView, "Mesh")
        tabwidget.addTab(label1, "Simulation")
        tabwidget.addTab(label1, "Spectrum")
        #self.progress.setValue(65)

        self.hLayout.addWidget(groupbox, 1)
        self.hLayout.addWidget(tabwidget, 2)
        self.vlayout.addLayout(self.hLayout)
        self.vlayout.addWidget(self.progress)
        #self.mesh.draw_grid()

    def meshButtonClick(self):
        pass
        #common.mesh.buildMesh()
        #self.mesh.deleteGrid()
        #self.mesh.drawGrid()
        #self.mesh.setOpacity(1)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.printer = QPrinter()

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Phonomena")
        self.resize(800, 600)

        self.main = Main()
        self.setCentralWidget(self.main)
        self.show()

    def open(self):
        options = QFileDialog.Options()
        # fileName = QFileDialog.getOpenFileName(self, "Open File", QDir.currentPath())
        fileName, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                  'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        if fileName:
            image = QImage(fileName)
            if image.isNull():
                QMessageBox.information(self, "Image Viewer", "Cannot load %s." % fileName)
                return

            self.imageLabel.setPixmap(QPixmap.fromImage(image))
            self.scaleFactor = 1.0

            self.scrollArea.setVisible(True)
            self.printAct.setEnabled(True)
            self.updateActions()

    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def about(self):
        QMessageBox.about(self, "Phonomena",
                          "<p>This program was developed for the ENPH 455 "
                          "undergraduate thesis by Marc Cameron and extended "
                          "by Matt Duke. It was designed to model acoustic "
                          "wave transmission using the FDTD simulation.</p>")

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.printAct = QAction("&Print...", self, shortcut="Ctrl+P", enabled=False, triggered=self.print_)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.aboutAct = QAction("&About", self, triggered=self.about)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
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

if __name__ == '__main__':
    common.import_settings("../../data/settings.ini")
    common.init()
    start()
