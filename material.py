import numpy as np

class Material:

    def __init__(self, size, grid, p1, c1, p2, c2):

        size_x, size_y, size_z = size
        self.C = np.zeros((size_x, size_y, size_z, 6, 6))
        self.P = np.zeros((size_x, size_y, size_z))

        self.set_dt(grid, p1, c1, p2, c2)

    '''
    Defines maximum speeds for parallel and transverse waves of each material
    Sets time step as mininum of time for material 1 and 2
    '''
    def set_dt(self, grid, p1, c1, p2, c2):
        g = grid
        (dt1, vl, vt) = self.set_coefficients(g, p1, c1)
        self.vl_bound = vl
        self.vt_bound = vt
        dt2 = 0
        if p2 is not None and c2 is not None:
            (dt2, vl, vt) = self.set_coefficients(g, p2, c2)

        if dt2 == 0:
            g.dt = dt1
        elif dt1 < dt2:
            g.dt = dt1
        else:
            g.dt = dt2

    def set_main_material(self, grid, p, c):

        g = grid

        # set update coefficients
        g.T2u[:,:,:] = g.dt**2/(g.dd*p)
        g.u2T = 1/g.dd

        # set P and C
        self.P[:,:,:] = p
        self.C[:,:,:] = c

        # set ABC coefficients
        vl = self.vl_bound
        vt = self.vt_bound
        self.abc_coef_long = (vl*g.dt-g.dd)/(vl*g.dt+g.dd)
        self.abc_coef_tran = (vt*g.dt-g.dd)/(vt*g.dt+g.dd)


    def set_inclusion_material(self, grid, p, c):
        #NEEDS WORK

        g = grid

        # set P and C
        # iterate over every 8th and 2nd element?
        length = int(g.size_x/8)
        width = int(g.size_y/2)
        for i in range(length,2*length):
            for j in range(int(width/2),int(3/2*width)):
                self.P[i,j,:] = p
                self.C[i,j,:] = c
                g.T2u[i,j,:] = g.dt**2/g.dd/p
        for i in range(3*length,4*length):
            for j in range(int(width/2),int(3/2*width)):
                self.P[i,j,:] = p
                self.C[i,j,:] = c
                g.T2u[i,j,:] = g.dt**2/g.dd/p
        for i in range(5*length,6*length):
            for j in range(int(width/2),int(3/2*width)):
                self.P[i,j,:] = p
                self.C[i,j,:] = c
                g.T2u[i,j,:] = g.dt**2/g.dd/p
        for i in range(7*length,8*length):
            for j in range(int(width/2),int(3/2*width)):
                self.P[i,j,:] = p
                self.C[i,j,:] = c
                g.T2u[i,j,:] = g.dt**2/g.dd/p

    def set_coefficients(self, g, p, c):

        # c is elastic stifness tensor
        c11 = c[0,0] # symmetric
        c44 = c[3,3]
        vl = np.sqrt(c11/p) # parallel
        vt = np.sqrt(c44/p) # transverse
        if vl > vt:
            vmax = vl
        else:
            vmax = vt
        dt = g.dd*g.sc/vmax
        return (dt, vl, vt)
