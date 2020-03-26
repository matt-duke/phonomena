import common
import numpy as np
import h5py
from time import sleep
from pathlib import Path
import shutil

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.lines import Line2D

from simulation import analysis

import logging
logger = logging.getLogger(__name__)


class Viewer(QWidget):
    def __init__(self, main_widget):
        super().__init__()

        self.main_widget = main_widget
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.ux_btn = QRadioButton("ux")
        self.ux_btn.setChecked(True)
        self.uy_btn = QRadioButton("uy")
        self.uz_btn = QRadioButton("uz")

        self.ux_btn.toggled.connect(self.layerChange)
        self.uy_btn.toggled.connect(self.layerChange)
        self.uz_btn.toggled.connect(self.layerChange)

        self.save_btn = QPushButton("Save HDF")
        self.save_btn.clicked.connect(self.saveHDFButton)
        self.open_btn = QPushButton("Open HDF")
        self.open_btn.clicked.connect(self.loadHDFButton)

        btn_l = QHBoxLayout()
        btn_l.addWidget(self.open_btn, alignment=QtCore.Qt.AlignLeft)
        btn_l.addWidget(self.save_btn, alignment=QtCore.Qt.AlignRight)
        margin = 15
        btn_l.setContentsMargins(margin,margin,margin,margin)

        self.layer_box = QGroupBox()
        self.layer_box.setTitle("Layer")
        layer_layout = QVBoxLayout()
        layer_layout.addWidget(self.ux_btn)
        layer_layout.addWidget(self.uy_btn)
        layer_layout.addWidget(self.uz_btn)
        self.layer_box.setLayout(layer_layout)

        self.plot_tab_widget = QTabWidget()
        canv_1 = FigureCanvas(Figure())
        self.disp_ax = canv_1.figure.subplots()
        self.disp_ax.axis('equal')
        canv_2 = FigureCanvas(Figure())
        self.density_ax = canv_2.figure.subplots()
        self.density_ax.axis('equal')
        canv_3 = FigureCanvas(Figure())
        self.spectrum_ax = canv_3.figure.subplots()
        self.plot_tab_widget.addTab(canv_1, "Displacement")
        self.plot_tab_widget.addTab(canv_2, "Density")
        self.plot_tab_widget.addTab(canv_3, "Spectrum")

        gb_fft = QGroupBox("Spectrum Gate")
        l_fft = QGridLayout()
        self.fft_slider = QSlider(QtCore.Qt.Orientation.Vertical)
        self.fft_slider.setTracking(False)
        self.fft_slider.setInvertedAppearance(True)
        self.fft_slider.valueChanged.connect(self.refresh)
        l_fft.addWidget(self.fft_slider)
        gb_fft.setLayout(l_fft)

        gb_z = QGroupBox("Z Slice")
        l_z = QGridLayout()
        self.z_slider = QSlider(QtCore.Qt.Orientation.Vertical)
        self.z_slider.setTracking(False)
        self.z_slider.setInvertedAppearance(True)
        self.z_slider.valueChanged.connect(self.refresh)
        l_z.addWidget(self.z_slider)
        gb_z.setLayout(l_z)

        gb_t = QGroupBox("Time Slice")
        l_t = QGridLayout()
        self.t_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.t_slider.setTracking(False)
        self.t_slider.valueChanged.connect(self.refresh)
        l_t.addWidget(self.t_slider)
        gb_t.setLayout(l_t)

        self.layout.addWidget(gb_fft,0,0)
        self.layout.addWidget(self.plot_tab_widget,0,1)
        self.layout.addWidget(self.layer_box,0,2)
        self.layout.addWidget(gb_t, 1, 0, 1, 2)
        self.layout.addWidget(gb_z, 0, 3)
        self.layout.addLayout(btn_l, 1, 2, 1, 2)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 5)
        self.layout.setColumnStretch(2, 1)
        self.layout.setColumnStretch(3, 1)

        margin = 30
        self.layout.setContentsMargins(margin,margin,margin,margin)
        self.layer_id = 'ux'

        self.hdf_file = None

    def loadHDF(self, file):
        file = Path(file)
        assert file.exists()
        self.hdf_file = file
        # test file
        with h5py.File(self.hdf_file,'r') as hdf:
            pass

    def loadHDFButton(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", QtCore.QDir.currentPath())
        if filename:
            try:
                self.loadHDF(filename)
                self.refresh()
            except:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Invalid file.")
                msg.setWindowTitle("Error")
                msg.exec_()

    def saveHDFButton(self):
        if self.hdf_file == None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("No HDF file loaded.")
            msg.setWindowTitle("Error")
            msg.exec_()
        else:
            filename, _ = QFileDialog.getSaveFileName(self, "Save File", QtCore.QDir.currentPath())
            if filename:
                shutil.copyfile(self.hdf_file, filename)

    def refresh(self):
        iz = lambda max: int(self.z_slider.value()/100*max)
        it = lambda max: int(self.t_slider.value()/100*max)
        ifft = lambda max: int(self.fft_slider.value()/100*max)
        if self.hdf_file != None:
            with h5py.File(self.hdf_file, mode='r') as hdf:
                u = hdf.get(self.layer_id)
                P = hdf.get('density')
                x = hdf.attrs['grid_x']
                y = hdf.attrs['grid_y']
                z = hdf.attrs['grid_z']

                x, f, fft = analysis.spectrum(
                    self.hdf_file,
                    y_index=ifft(y.size),
                    z_index=iz(z.size)
                )
                FFT = np.real(fft)
                F, X = np.meshgrid(f, x)
                fig = self.spectrum_ax.figure
                fig.clear()
                self.spectrum_ax = fig.subplots()
                cf = self.spectrum_ax.contourf(X, F, FFT, 100)
                self.spectrum_ax.figure.colorbar(cf)
                self.spectrum_ax.figure.canvas.draw()

                X, Y = np.meshgrid(y, x)
                fig = self.density_ax.figure
                fig.clear()
                self.density_ax = fig.subplots()
                self.density_ax.axis('equal')
                Z = P[:,:,iz(P.shape[2])]
                cf = self.density_ax.contourf(X, Y, Z, 100)
                self.density_ax.figure.colorbar(cf)
                self.density_ax.figure.canvas.draw()

                size_x, size_y = (u.shape[0], u.shape[1])
                X, Y = np.meshgrid(y[:size_y], x[:size_x])
                self.disp_ax.clear()
                Z = u[:,:,iz(u.shape[2]),it(u.shape[3])]
                self.disp_ax.contourf(X, Y, Z, 100)
                self.disp_ax.figure.canvas.draw()
        else:
            x, y = common.grid.x, common.grid.y
            X, Y = np.meshgrid(y, x)
            P = common.material.P

            X, Y = np.meshgrid(y, x)
            self.density_ax.clear()
            self.density_ax.contourf(X, Y, P[:,:,iz(P.shape[2])])
            self.density_ax.figure.canvas.draw()

    def layerChange(self):
        btn = [self.ux_btn,self.uy_btn,self.uz_btn]
        for b in btn:
            if b.isChecked():
                self.layer_id = b.text()
                break
        self.refresh()
