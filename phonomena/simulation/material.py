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

import numpy as np

class Material:

    def __init__(self, grid, propeties):
        self.grid = grid
        self.propeties = propeties

        self.primary = None
        self.secondary = None

        self.C = np.array(())
        self.P = np.array(())

        self.c_max = 1 #courant number
        self.dt = 0

        self.C = np.zeros((0,0,0,6,6))
        self.P = np.zeros((0,0,0))

        self.T2ux = np.zeros((0,0,0))
        self.T2uy = np.zeros((0,0,0))
        self.T2uz = np.zeros((0,0,0))
        self.ux2T = 0
        self.uy2T = 0
        self.uz2T = 0

    def update(self):
        self.C = np.zeros((self.grid.x.size, self.grid.y.size, self.grid.z.size, 6, 6))
        self.P = np.zeros((self.grid.x.size, self.grid.y.size, self.grid.z.size))

        self.setTimeStep()
        self.setConstants()

    def setConstants(self):
        self.C[:,:,:] = np.array(self.primary['c'])*1e10
        self.P[:,:,:] = float(self.primary['p'])

        Ixy, Iz = self.grid.inclusionIndices()
        for iz in Iz:
            for ix, iy in Ixy:
                self.C[ix,iy,iz] = np.array(self.secondary['c'])
                self.P[ix,iy,iz] = float(self.secondary['p'])
                #modify T2u values

    def setMaterials(self, m1, m2):
        self.primary = self.propeties[m1]
        self.secondary = self.propeties[m2]

    ''' Set simulation timestep based on Courant–Friedrichs–Lewy condition '''
    def setTimeStep(self):
        def calcDt(c, p):
            c11 = c[0][0]
            c44 = c[3][3]
            vl = np.sqrt(c11/p) # parallel
            vt = np.sqrt(c44/p) # transverse
            vmax = max((vl, vt))
            dtx = self.grid.fdx[:,0,0]*self.c_max/vmax
            dty = self.grid.fdy[0,:,0]*self.c_max/vmax
            dtz = self.grid.fdz[0,0,:]*self.c_max/vmax
            return np.amin(np.concatenate((dtx, dty, dtz)))

        dt1 = calcDt(self.primary['c'], self.primary['p'])
        dt2 = calcDt(self.secondary['c'], self.secondary['p'])
        self.dt = min((dt1, dt2))
        print(self.dt)
        self.dt = 0.00001

if __name__ == '__main__':
    import common
    common.importSettings()
    common.init()
