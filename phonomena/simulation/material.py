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
import logging
from threading import Lock
logger = logging.getLogger(__name__)

class Material:

    def __init__(self):
        self.primary = None
        self.secondary = None

        self.c_max = 0.5 #courant number
        self.dt = 0

        self.C = np.zeros((0,0,0,6,6))
        self.P = np.zeros((0,0,0))

        self.lock = Lock()

    def init(self, grid, properties):
        self.grid = grid
        self.properties = properties
        for key, val in self.properties.items():
            val['c'] = np.array(val['c'])*1e10

    def update(self):
        self.C = np.zeros((self.grid.x.size, self.grid.y.size, self.grid.z.size, 6, 6))
        self.P = np.zeros((self.grid.x.size, self.grid.y.size, self.grid.z.size))

        self.setTimeStep()
        self.setConstants()

    def setConstants(self):
        self.C[:,:,:] = np.array(self.primary['c'])
        self.P[:,:,:] = float(self.primary['p'])

        I = self.grid.inclusionIndices()
        for xy, z in I:
            for x, y in xy:
                self.C[x,y,z] = np.array(self.secondary['c'])
                self.P[x,y,z] = float(self.secondary['p'])

    def setPrimary(self, m):
        if m in self.properties.keys():
            self.primary = self.properties[m]
        else:
            raise Exception()

    def setSecondary(self, m):
        if m in self.properties.keys():
            self.secondary = self.properties[m]
        else:
            raise Exception()

    ''' Set simulation timestep based on Courant–Friedrichs–Lewy condition '''
    def setTimeStep(self):
        def calcDt(c, p):
            c11 = c[0][0]
            c44 = c[3][3]
            vl = np.sqrt(c11/p) # parallel
            vt = np.sqrt(c44/p) # transverse
            vmax = max((vl, vt))
            dxmin = min((np.amin(self.grid.fdx),np.amin(self.grid.fdy), np.amin(self.grid.fdz)))
            dt = self.c_max*dxmin/vmax
            return dt

        dt1 = calcDt(self.primary['c'], self.primary['p'])
        dt2 = calcDt(self.secondary['c'], self.secondary['p'])
        self.dt = min((dt1, dt2))


if __name__ == '__main__':
    import common
    common.importSettings()
    common.init()
