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

class Grid:

    def __init__(self):
        self.lock = Lock()
        self.x = np.array((), dtype=np.float)
        self.y = np.array((), dtype=np.float)
        self.z = np.array((), dtype=np.float)

        self.max_dx = 1
        self.max_dy = 1
        self.max_dz = 1

        self.trgt_dtype=np.dtype([('x','f'), ('y','f'), ('z','f'), ('r','f')])
        self.targets = np.empty((0,0), self.trgt_dtype)
        self.min_d = 0.1
        self.slope = 0.5

    def init(self, size_x, size_y, size_z, spacing_fn=None):

        self.size_x = int(size_x)
        self.size_y = int(size_y)
        self.size_z = int(size_z)

        if spacing_fn == None:
            self.spacing_fn = lambda x: abs(x * self.slope)
        else:
            self.spacing_fn = spacing_fn

        self.buildMesh()
        self.update()

    def update(self):
        x = self.x.size
        y = self.y.size
        z = self.z.size

        self.ux = np.zeros((x-1, y, z), dtype=np.float64)
        self.uy = np.zeros((x, y-1, z), dtype=np.float64)
        self.uz = np.zeros((x, y, z-1), dtype=np.float64)

        self.ux_new = np.zeros((x-1, y, z), dtype=np.float64)
        self.uy_new = np.zeros((x, y-1, z), dtype=np.float64)
        self.uz_new = np.zeros((x, y, z-1), dtype=np.float64)

        self.ux_old = np.zeros((x-1, y, z), dtype=np.float64)
        self.uy_old = np.zeros((x, y-1, z), dtype=np.float64)
        self.uz_old = np.zeros((x, y, z-1), dtype=np.float64)

        self.ux_temp = np.zeros((x-1, y, z), dtype=np.float64)
        self.uy_temp = np.zeros((x, y-1, z), dtype=np.float64)
        self.uz_temp = np.zeros((x, y, z-1), dtype=np.float64)

        self.T1 = np.zeros((x, y, z), dtype=np.float64)
        self.T2 = np.zeros((x, y, z), dtype=np.float64)
        self.T3 = np.zeros((x, y, z), dtype=np.float64)
        self.T4 = np.zeros((x, y-1, z-1), dtype=np.float64)
        self.T5 = np.zeros((x-1, y, z-1), dtype=np.float64)
        self.T6 = np.zeros((x-1, y-1, z), dtype=np.float64)

        # full dx (n-1)
        self.fdx = (self.x[1:] - self.x[:-1]).reshape((x-1,1,1))
        self.fdy = (self.y[1:] - self.y[:-1]).reshape((1,y-1,1))
        self.fdz = (self.z[1:] - self.z[:-1]).reshape((1,1,z-1))

        # staggered dx (n-2)
        self.sdx = np.mean([self.fdx[1:,:,:], self.fdx[:-1,:,:]], axis=0)
        #print(self.sdx.shape)
        self.sdy = np.mean([self.fdy[:,1:,:], self.fdy[:,:-1,:]], axis=0)
        #print(self.sdy.shape)
        self.sdz = np.mean([self.fdz[:,:,1:], self.fdz[:,:,:-1]], axis=0)
        #print(self.sdz.shape)

    def clearMesh(self):
        self.x = np.array((), dtype=np.float)
        self.y = np.array((), dtype=np.float)
        built = False

    def clearInclusions(self):
        self.targets = np.empty((0,0), self.trgt_dtype)

    def addInclusion(self, x, y, r, z=None):
        if z == None:
            z = self.size_z
        target = np.array([(x,y,z,r)], dtype=self.trgt_dtype)
        self.targets = np.append(self.targets, target)

    def inclusionIndices(self):
        #import sys
        #np.set_printoptions(threshold=sys.maxsize)
        I = list()
        Y, X = np.meshgrid(self.y, self.x)
        for t in self.targets:
            #Ixy = np.empty((0,2), dtype=np.int)
            #Iz = np.empty((1,0), dtype=np.int)
            Xsq = np.square(np.subtract(X, t['x']))
            Ysq = np.square(np.subtract(Y, t['y']))
            R = np.sqrt(np.add(Xsq, Ysq))
            xy = np.array(np.where(R<=t['r'])).transpose()
            assert np.all(xy < R.shape)
            z = np.array(np.where(self.z<=t['z'])).flatten()
            I.append((xy, z))
            #Iz = np.append(Iz, z, axis=1)
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
            overlap = np.absolute(np.subtract(arr[0:-1], arr[1:]))
            indices = np.add(np.where(overlap < self.min_d), 1)
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
                n = int(round(t['r']*2 / self.min_d)) - 1
                fn = lambda var: (t['r']*2 / n) * (var+1) + t[axis] - t['r']
                mesh = appendSorted(mesh, np.fromfunction(fn, (n,)))

            return mesh

        # return dummy signals if not passed to function
        signals = WorkerSignals() if 'signals' not in kwargs.keys() else kwargs['signals']
        signals.status.emit("Rebuilding mesh...")
        signals.progress.emit(0)
        # Add first and last mesh points
        self.clearMesh()

        # Add/update X lines
        self.x = appendSorted(self.x, 0)
        self.x = appendSorted(self.x, self.size_x)
        if len(self.targets) > 0:
            signals.status.emit("Area around inclusion regions...")
            self.x = appendSorted(self.x, functionMesh('x'))
            signals.status.emit("Filling inclusion regions...")
            self.x = appendSorted(self.x, fillInclusion('x'))
            self.x = removeClose(self.x)
        signals.status.emit("X mesh completed...")
        self.x = appendSorted(self.x, closestFit('x'))

        # Add/update Y lines
        self.y = appendSorted(self.y, 0)
        self.y = appendSorted(self.y, self.size_y)

        if len(self.targets) > 0:
            self.y = appendSorted(self.y, functionMesh('y'))
            self.y = appendSorted(self.y, closestFit('y'))
            self.y = appendSorted(self.y, fillInclusion('y'))
            self.y = removeClose(self.y)
        self.y = appendSorted(self.y, closestFit('y'))

        # Add/update Z lines. Uniform constant mesh spacing
        n = int(self.size_z / self.max_dz)
        self.z = np.linspace(0, self.size_z, n+1, dtype=np.float)

        self.built = True

if __name__ == '__main__':
    g = Grid(4, 4, 4)
    g.buildMesh()
    g.update()
