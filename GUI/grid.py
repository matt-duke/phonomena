import numpy as np
from collections import namedtuple
import math as m

class Grid:

    def __init__(self, size_x, size_y, size_z):
        self.size_x = size_x
        self.size_y = size_y
        self.size_z = size_z

        self.default_dx = 1
        self.default_dy = 1

        self.x = np.array((), dtype=np.float)
        self.y = np.array((), dtype=np.float)

        self.targets = None

    def addInclusion(self, x, y, r):
        dtype=np.dtype([('x','f'), ('y','f'), ('r','f')])
        target = np.array([(x,y,r)], dtype=dtype)
        if type(self.targets) == type(None):
            self.targets = target
        else:
            self.targets = np.append(self.targets, target)

    def buildMesh(self, function, min_d):

        def appendSorted(arr, values):
            # only keep values not in main array
            values = np.setdiff1d(values, arr)
            arr = np.append(arr, values)
            arr.sort()
            return arr

        def fineMesh(max_d):
            fine_mesh = np.array((0,))
            dx = 0
            while dx < max_d:
                dx = function(fine_mesh[-1] + min_d) + min_d
                if dx < max_d:
                    fine_mesh = np.append(fine_mesh, fine_mesh[-1] + dx)

            return fine_mesh

        def removeClose(arr):
            # Remove mesh points that are too close together
            overlap = np.absolute(np.subtract(arr[0:-1], arr[1:]))
            indices = np.add(np.where(overlap < min_d), 1)
            arr = np.delete(arr, indices)
            return arr

        def functionMesh(axis):
            axis = axis.lower()
            assert axis == 'x' or axis == 'y'
            default_d = {'x': self.default_dx, 'y': self.default_dy}[axis]
            size = {'x': self.size_x, 'y': self.size_y}[axis]
            global_mesh = {'x': self.x, 'y': self.y}[axis]
            fine_mesh = fineMesh(default_d)
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
                    x2 = self.size_x
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
            default_d = {'x': self.default_dx, 'y': self.default_dy}[axis]
            mesh = np.array(())
            for i in range(1, len(global_mesh)):
                n = int(round(abs(global_mesh[i] - global_mesh[i-1]) / default_d)) - 1
                if n > 0:
                    fn = lambda var: abs(global_mesh[i] - global_mesh[i-1]) / n * (var+1) + global_mesh[i-1]
                    mesh = appendSorted(mesh, np.fromfunction(fn, (n,)))
                    #print(self.x[i-1], self.x[i], n, mesh)
            return mesh

        def fillInclusion(axis):
            # Fill inclusion regions with fine mesh
            axis = axis.lower()
            assert axis == 'x' or axis == 'y'
            mesh = np.array(())
            for t in self.targets:
                n = int(round(t['r']*2 / min_d)) - 1
                fn = lambda var: (t['r']*2 / n) * (var+1) + t[axis] - t['r']
                mesh = appendSorted(mesh, np.fromfunction(fn, (n,)))

            return mesh

        # Add first and last mesh points
        self.x = appendSorted(self.x, 0)
        self.x = appendSorted(self.x, self.size_x)
        self.x = appendSorted(self.x, functionMesh('x'))
        self.x = appendSorted(self.x, fillInclusion('x'))
        self.x = removeClose(self.x)
        self.x = appendSorted(self.x, closestFit('x'))

        print(self.x)

        self.y = appendSorted(self.y, 0)
        self.y = appendSorted(self.y, self.size_y)
        self.y = appendSorted(self.y, functionMesh('y'))
        self.y = appendSorted(self.y, closestFit('y'))
        self.y = appendSorted(self.y, fillInclusion('y'))
        self.y = removeClose(self.y)

        #check overlap distances
        #overlap = np.absolute(np.subtract(self.y[0:-1], self.x[1:]))
        #print(overlap)

if __name__ == '__main__':
    g = Grid(20, 20, 5)
    g.addInclusion(5,15,0.5)
    g.addInclusion(15,5,0.5)
    g.buildMesh(lambda x: 0.2*x, 0.15)
