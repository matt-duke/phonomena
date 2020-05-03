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
import math as m
from threading import Lock

from gui.worker import WorkerSignals

DTYPE = np.float64

class FrozenGrid:
    ux = None
    uy = None
    uz = None


class Grid:

    '''
    Grid class stores mesh information and includes function for building a non-uniform mesh.
    '''

    def __init__(self):
        '''
        Basic object creation. init() method should also be called to setup the grid object
        '''
        self.trgt_dtype=np.dtype([('x','f'), ('y','f'), ('z','f'), ('r','f')])
        self.max_dx = 1
        self.max_dy = 1
        self.max_dz = 1
        self.min_d = 1 # Defualts to uniform array
        self.slope = 1

        self.SI_conversion = 1 # all variables stored in mm

        self.clearMesh() # Initialize mesh arrays
        self.clearInclusions() # Initialize targets array

    def init(self, size_x, size_y, size_z, fn='linear'):
        '''
        Pass grid specifics and initialize object variables.
        Future versions can add additional spacing functions (x**2, exp, 1/x, etc.)
        '''

        spacing_fns = {'linear': lambda x: abs(x * self.slope)}

        self.size_x = int(size_x)
        self.size_y = int(size_y)
        self.size_z = int(size_z)

        self.spacing_fn = spacing_fns[fn]

        self.buildMesh()
        self.update()

    def freezeData(self):
        '''
        Used to freeze grid data and return object emulating minimal Grid class
        For transferring data to other threads
        '''
        fg = FrozenGrid()
        fg.ux = np.copy(self.ux)
        fg.uy = np.copy(self.uy)
        fg.uz = np.copy(self.uz)
        return fg

    def update(self):
        '''
        Create mesh data used in simualtion once all variables are set (manually and using buildMesh())
        '''
        x = self.x.size
        y = self.y.size
        z = self.z.size

        # Displacement matrices (Highest precision)
        self.ux = np.zeros((x-1, y, z), dtype=DTYPE)
        self.uy = np.zeros((x, y-1, z), dtype=DTYPE)
        self.uz = np.zeros((x, y, z-1), dtype=DTYPE)

        self.ux_new = np.zeros((x-1, y, z), dtype=DTYPE)
        self.uy_new = np.zeros((x, y-1, z), dtype=DTYPE)
        self.uz_new = np.zeros((x, y, z-1), dtype=DTYPE)

        self.ux_old = np.zeros((x-1, y, z), dtype=DTYPE)
        self.uy_old = np.zeros((x, y-1, z), dtype=DTYPE)
        self.uz_old = np.zeros((x, y, z-1), dtype=DTYPE)

        self.ux_temp = np.zeros((x-1, y, z), dtype=DTYPE)
        self.uy_temp = np.zeros((x, y-1, z), dtype=DTYPE)
        self.uz_temp = np.zeros((x, y, z-1), dtype=DTYPE)

        # Stress tensor
        self.T1 = np.zeros((x, y, z), dtype=DTYPE)
        self.T2 = np.zeros((x, y, z), dtype=DTYPE)
        self.T3 = np.zeros((x, y, z), dtype=DTYPE)
        self.T4 = np.zeros((x, y-1, z-1), dtype=DTYPE)
        self.T5 = np.zeros((x-1, y, z-1), dtype=DTYPE)
        self.T6 = np.zeros((x-1, y-1, z), dtype=DTYPE)

        # fd and sd must be in SI units for calculation. Converted here.
        x_SI = self.x * self.SI_conversion
        y_SI = self.y * self.SI_conversion
        z_SI = self.z * self.SI_conversion

        # full dx (n-1)
        self.fdx = (x_SI[1:] - x_SI[:-1]).reshape((x-1,1,1))
        self.fdy = (y_SI[1:] - y_SI[:-1]).reshape((1,y-1,1))
        self.fdz = (z_SI[1:] - z_SI[:-1]).reshape((1,1,z-1))

        # staggered dx (n-2)
        self.sdx = np.mean([self.fdx[1:,:,:], self.fdx[:-1,:,:]], axis=0)
        #print(self.sdx.shape)
        self.sdy = np.mean([self.fdy[:,1:,:], self.fdy[:,:-1,:]], axis=0)
        #print(self.sdy.shape)
        self.sdz = np.mean([self.fdz[:,:,1:], self.fdz[:,:,:-1]], axis=0)
        #print(self.sdz.shape)

    def clearMesh(self):
        '''
        Clear mesh data. Resets dimesnion arrays
        '''
        self.x = np.array((), dtype=DTYPE)
        self.y = np.array((), dtype=DTYPE)
        self.z = np.array((), dtype=DTYPE)

    def clearInclusions(self):
        '''
        Remove all inclusion regions
        '''
        self.targets = np.empty((0,0), self.trgt_dtype)

    def addInclusion(self, x, y, r, z=None):
        '''
        Add inclusion region where units are passed in mm
        '''
        x = float(x)
        y = float(y)
        r = float(r)
        assert x+r < self.size_x and x-r > 0
        assert y+r < self.size_y and y-r > 0
        if z == None:
            z = self.size_z
        target = np.array([(x,y,z,r)], dtype=self.trgt_dtype)
        self.targets = np.append(self.targets, target)

    def inclusionIndices(self):
        #import sys
        #np.set_printoptions(threshold=sys.maxsize)
        I = list()

        x, y, z = self.x, self.y, self.z
        for t in self.targets:
            X, Y = np.meshgrid(x, y)
            X = X - t['x']
            Y = Y - t['y']
            Xsq = np.square(X)
            Ysq = np.square(Y)
            R = np.sqrt(np.add(Xsq, Ysq))
            yx = np.array(np.where(R<t['r'])).transpose()
            assert np.all(yx < R.shape)
            z = np.array(np.where(z<=t['z'])).flatten()
            I.append((yx, z))
        return I

    def buildMesh(self, *args, **kwargs):

        def appendSorted(arr, values):
            # only keep values not already in main array
            values = np.setdiff1d(values, arr)
            arr = np.append(arr, values)
            arr.sort()
            return arr

        def fineMesh(max_d):
            fine_mesh = np.array((0,))
            dx = 0
            while dx < max_d:
                dx = self.spacing_fn(fine_mesh[-1] + self.min_d) + self.min_d
                if dx < max_d:
                    fine_mesh = np.append(fine_mesh, fine_mesh[-1] + dx)

            return fine_mesh

        def removeClose(arr):
            # Remove mesh points that are too close together
            allowance = 0.9
            overlap = np.absolute(np.subtract(arr[0:-1], arr[1:]))
            indices = np.add(np.where(overlap < allowance*self.min_d), 1)
            arr = np.delete(arr, indices)
            return arr

        def functionMesh(axis):
            axis = axis.lower()
            assert axis == 'x' or axis == 'y'
            max_d = {'x': self.max_dx, 'y': self.max_dy}[axis]
            size = {'x': self.size_x, 'y': self.size_y}[axis]
            global_mesh = {'x': self.x, 'y': self.y}[axis]
            fine_mesh = fineMesh(max_d)
            t = np.sort(self.targets, order=axis)
            mesh = np.array(())
            # Add mesh to right and left of inclusion region

            for i in range(len(t)):
                x1, x2 = None, None
                # This is the first
                if t[i][axis] == t[0][axis]:
                    x1 = 0
                elif len(t) > 1:
                    x1 = t[i][axis] - t[i][axis] - (t[i][axis] - t[i-1][axis]) / 2
                else:
                    raise Exception("Neither condition met")
                if t[i][axis] == t[-1][axis]:
                    x2 = size
                elif len(t) > 1:
                    #find midpoint
                    x2 = (t[i+1][axis] - t[i][axis]) / 2 + t[i][axis] + t[i]['r']
                else:
                    raise Exception("Neither condition met")

                #right side fine mesh
                mesh = appendSorted(mesh, t[i][axis] + t[i]['r'] + fine_mesh)
                #left side fine mesh
                mesh = appendSorted(mesh, t[i][axis] - t[i]['r'] - fine_mesh)

                #Clear mesh points outside bounds
                mesh = mesh[np.greater_equal(mesh, 0)]
                mesh = mesh[np.greater_equal(mesh, x1)]
                mesh = mesh[np.less_equal(mesh, x2)]
                mesh = mesh[np.less_equal(mesh, size)]

            return mesh

        def closestFit(axis):
            # Create closest fit mesh for large spaces
            axis = axis.lower()
            assert axis == 'x' or axis == 'y'
            global_mesh = {'x': self.x, 'y': self.y}[axis]
            max_d = {'x': self.max_dx, 'y': self.max_dy}[axis]
            mesh = np.array(())
            for i in range(1, len(global_mesh)):
                n = int(abs(global_mesh[i] - global_mesh[i-1]) / max_d)
                if n > 0:
                    n = n+1
                    #fn = lambda var: abs(global_mesh[i] - global_mesh[i-1]) / n * (var+1) + global_mesh[i-1]
                    #mesh = appendSorted(mesh, np.fromfunction(fn, (n,)))
                    temp = np.linspace(global_mesh[i-1], global_mesh[i], n, dtype=np.float)
                    mesh = appendSorted(mesh, temp)
                    #print(self.x[i-1], self.x[i], n, mesh)
            return mesh

        def fillInclusion(axis):
            # Fill inclusion regions with fine mesh
            axis = axis.lower()
            assert axis == 'x' or axis == 'y'
            mesh = np.array(())
            for t in self.targets:
                n = int(m.floor(t['r']*2 / self.min_d))
                fn = lambda var: (t['r']*2 / n) * var + t[axis] - t['r']
                mesh = appendSorted(mesh, np.fromfunction(fn, (n+1,)))

            return mesh

        # return dummy signals if not passed to function
        signals = WorkerSignals() if 'signals' not in kwargs.keys() else kwargs['signals']
        signals.status.emit("Rebuilding mesh...")
        # Add first and last mesh points
        self.clearMesh()

        # Add/update X lines
        self.x = appendSorted(self.x, 0)
        self.x = appendSorted(self.x, self.size_x)
        if len(self.targets) > 0:
            self.x = appendSorted(self.x, fillInclusion('x'))
            self.x = appendSorted(self.x, functionMesh('x'))
            self.x = removeClose(self.x)
        self.x = appendSorted(self.x, closestFit('x'))

        # Add/update Y lines
        self.y = appendSorted(self.y, 0)
        self.y = appendSorted(self.y, self.size_y)
        if len(self.targets) > 0:
            self.y = appendSorted(self.y, fillInclusion('y'))
            self.y = appendSorted(self.y, functionMesh('y'))
            self.y = removeClose(self.y)
        self.y = appendSorted(self.y, closestFit('y'))

        # Add/update Z lines. Uniform constant mesh spacing
        n = int(self.size_z / self.max_dz)
        self.z = np.linspace(0, self.size_z, n+1, dtype=np.float)

        signals.status.emit("Completed mesh.")

if __name__ == '__main__':
    import matplotlib
    import matplotlib.pyplot as plt
    g = Grid()
    g.max_dx = 1
    g.max_dy = 1
    g.max_dz = 1
    g.min_d = 0.8
    g.slope = 1
    g.init(20, 20, 5)
    g.addInclusion(15, 15, 1)
    g.addInclusion(9.5, 5, 2)
    g.buildMesh()
    g.update()

    R = g.inclusionIndices()
    fig, ax = plt.subplots()
    cf = ax.contourf(g.x, g.y, R)
    plt.colorbar(cf)
    plt.axis('equal')
    plt.show()

    '''fig, ax = plt.subplots()
    x = [t['x'] for t in g.targets]
    y = [t['y'] for t in g.targets]
    ax.scatter(x,y)
    ax.set_xlim((0,g.size_x))
    ax.set_ylim((0,g.size_y))
    ax.set_xticks(g.x)
    ax.set_yticks(g.y)
    plt.grid()
    plt.show()'''
