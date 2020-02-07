import numpy as np

class Grid:

    def __init__(self, size):

        self.size_x, self.size_y, self.size_z = size
        size_x, size_y, size_z = size

        self.ux = np.zeros((size_x-1, size_y, size_z))
        self.uy = np.zeros((size_x, size_y-1, size_z))
        self.uz = np.zeros((size_x, size_y, size_z-1))

        self.ux_new = np.zeros((size_x-1, size_y, size_z))
        self.uy_new = np.zeros((size_x, size_y-1, size_z))
        self.uz_new = np.zeros((size_x, size_y, size_z-1))

        self.ux_old = np.zeros((size_x-1, size_y, size_z))
        self.uy_old = np.zeros((size_x, size_y-1, size_z))
        self.uz_old = np.zeros((size_x, size_y, size_z-1))

        self.ux_temp = np.zeros((size_x-1, size_y, size_z))
        self.uy_temp = np.zeros((size_x, size_y-1, size_z))
        self.uz_temp = np.zeros((size_x, size_y, size_z-1))

        self.T1 = np.zeros((size_x, size_y, size_z))
        self.T2 = np.zeros((size_x, size_y, size_z))
        self.T3 = np.zeros((size_x, size_y, size_z))
        self.T4 = np.zeros((size_x, size_y-1, size_z-1))
        self.T5 = np.zeros((size_x-1, size_y, size_z-1))
        self.T6 = np.zeros((size_x-1, size_y-1, size_z))

        self.dd = 1
        self.dt = 0
        self.sc = 1/(np.sqrt(3)*1.5)
        self.T2u = np.zeros((size_x, size_y, size_z))
        self.u2T = 0
