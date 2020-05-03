import common
import numpy as np
import h5py
from time import sleep
from pathlib import Path
import shutil
import math as m

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.lines import Line2D
import matplotlib.ticker as ticker

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
        self.density_ax = canv_1.figure.subplots()

        canv_2 = FigureCanvas(Figure())
        self.disp_ax = canv_2.figure.subplots()

        canv_3 = FigureCanvas(Figure())
        self.spectrum1D_ax = canv_3.figure.subplots()

        canv_4 = FigureCanvas(Figure())
        self.spectrum2D_ax = canv_4.figure.subplots()

        self.plot_tab_widget.addTab(canv_1, "Density")
        self.plot_tab_widget.addTab(canv_2, "Displacement")
        self.plot_tab_widget.addTab(canv_3, "Spectrum 1D")
        self.plot_tab_widget.addTab(canv_4, "Spectrum 2D")

        gb_fft = QGroupBox("Spectrum Gate")
        l_fft = QGridLayout()
        self.fft_slider = QSlider(QtCore.Qt.Orientation.Vertical)
        self.fft_slider.setTracking(False)
        self.fft_slider.setInvertedAppearance(False)
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
        self.u_id = 'ux'

        self.hdf_file = None

        self.iz = lambda max: int(self.z_slider.value()/100*max)
        self.it = lambda max: int(self.t_slider.value()/100*max)
        self.ifft = lambda max: int(self.fft_slider.value()/100*max)

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

    def clear(self):
        self.hdf = None

    def showError(self, e):
        self.main_widget.window.showError(e)

    def plotDft1D(self, hdf, x, y, z, shape):
        try:
            ix, iy, iz = self.ifft(shape[0]), int(shape[1]/2), self.iz(shape[2])
            x, f, dft = analysis.spectrum(
                hdf,
                u_id = self.u_id,
                x_index=ix,
                y_index=iy,
                z_index=iz
            )
            dft, I = analysis.trim_trailing_zeros(dft, threshold=1)
            self.spectrum1D_ax.figure.clear()
            self.spectrum1D_ax = self.spectrum1D_ax.figure.subplots()
            cf = self.spectrum1D_ax.plot(f[I], dft)
            self.spectrum1D_ax.set_xlabel('Frequency [Hz]')
            self.spectrum1D_ax.set_ylabel('DFT')
            self.spectrum1D_ax.set_title('1D FFT (t) of {} at x={:.2f}, y={:.2f}, z={:.2f}'.format(self.u_id, x[ix], y[iy], z[iz]))
            self.spectrum1D_ax.figure.canvas.draw()
        except Exception as e:
            self.showError(e)

    def plotDft2D(self, hdf, x, y, z, shape):
        try:
            iy, iz = self.ifft(shape[1]), self.iz(shape[2])
            x, f, dft = analysis.spectrum(
                hdf,
                u_id = self.u_id,
                y_index=iy,
                z_index=iz
            )
            dft, I = analysis.trim_trailing_zeros(dft, threshold=1)
            self.spectrum2D_ax.figure.clear()
            self.spectrum2D_ax = self.spectrum2D_ax.figure.subplots()
            X, F = np.meshgrid(x, f[I])
            cf = self.spectrum2D_ax.contourf(X, F, dft.transpose(), 100)
            self.spectrum2D_ax.figure.colorbar(cf)
            self.spectrum2D_ax.set_xlabel('X [mm]')
            ticks = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x*1e3))
            self.spectrum2D_ax.xaxis.set_major_formatter(ticks)
            self.spectrum2D_ax.set_ylabel('Frequency [Hz]')
            self.spectrum2D_ax.set_title('2D FFT (x, t) of {} at y={:.2f}, z={:.2f}'.format(self.u_id, y[iy], z[iz]))
            self.spectrum2D_ax.figure.canvas.draw()
        except Exception as e:
            self.showError(e)

    def plotDensity(self, x, y, z, P):
        try:
            iz = self.iz(P.shape[2])
            x = np.mean([x[:-1], x[1:]], axis=0)
            y = np.mean([y[:-1], y[1:]], axis=0)
            X, Y = np.meshgrid(x,y)
            Z = P[1:-1,1:-1,iz].transpose()
            self.density_ax.figure.clear()
            self.density_ax = self.density_ax.figure.subplots()
            cf = self.density_ax.pcolormesh(X, Y, Z)
            self.density_ax.set_xticks(x)
            self.density_ax.set_xticklabels([])
            self.density_ax.set_yticklabels([])
            self.density_ax.set_yticks(y)
            self.density_ax.grid()
            self.density_ax.axis('equal')
            self.density_ax.set_xlabel('X [mm]')
            self.density_ax.set_ylabel('Y [mm]')
            self.density_ax.set_title('density at z={:.2f}'.format(iz))
            self.density_ax.figure.colorbar(cf)
            self.density_ax.figure.canvas.draw()
        except Exception as e:
            self.showError(e)

    def plotDisplacement(self, x, y, z, u, dt):
        try:
            iz, it = self.iz(u.shape[2]), self.it(u.shape[3])
            size_x, size_y = (u.shape[0], u.shape[1])
            print(u.size)
            X, Y = np.meshgrid(x[:size_x], y[:size_y])
            self.disp_ax.figure.clear()
            self.disp_ax = self.disp_ax.figure.subplots()
            Z = u[:,:,iz,it].transpose()
            cf = self.disp_ax.contourf(X, Y, Z, 100)
            self.disp_ax.figure.colorbar(cf)
            self.disp_ax.set_xlabel('X [mm]')
            self.disp_ax.set_ylabel('Y [mm]')
            self.disp_ax.set_title('{} at z={:.2f}, t={:.2f}ms'.format(self.u_id, z[iz], it*dt*1e3))
            self.disp_ax.figure.canvas.draw()
        except Exception as e:
            self.showError(e)

    def refresh(self):
        if self.hdf_file != None:
            with h5py.File(self.hdf_file, mode='r') as hdf:
                u = hdf.get(self.u_id)
                P = hdf.get('density')
                x = hdf.attrs['x']
                y = hdf.attrs['y']
                z = hdf.attrs['z']
                dt = hdf.attrs['dt']

                # Seperate update functions for speed. No need to run all calculations for every change
                sender = self.sender()
                if sender == self.t_slider:
                    self.plotDisplacement(x,y,z,u,dt)
                elif sender == self.fft_slider:
                    self.plotDft1D(hdf, x, y, z, u.shape)
                    #self.plotDft2D(hdf, x, y, z, u.shape)
                #elif sender == self.z_slider:
                else:
                    self.plotDensity(x,y,z,P)
                    self.plotDft1D(hdf, x, y, z, u.shape)
                    #self.plotDft2D(hdf, x, y, z, u.shape)
                    self.plotDisplacement(x,y,z,u,dt)
        else:
            self.plotDensity(
                common.grid.x,
                common.grid.y,
                common.grid.z,
                common.material.P
            )

    def layerChange(self):
        btn = [self.ux_btn,self.uy_btn,self.uz_btn]
        for b in btn:
            if b.isChecked():
                self.u_id = b.text()
                break
        self.refresh()
