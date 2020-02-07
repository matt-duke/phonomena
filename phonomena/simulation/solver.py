import numpy as np

class Solver:

    def __init__(self, grid, material):
        self.g = grid
        self.m = material

    def update_ricker(self, tt):

        # define constants for ricker wave
        ppw = 20
        source_delay = 0

        # create ricker wave
        arg = (np.pi*((self.g.sc*tt - source_delay)/ppw - 1.0)) ** 2
        ricker = (1 - 2 * arg) * np.exp(-arg)
        return ricker

    def update_delta(self, tt):

        source_delay = 0
        if tt == source_delay:
            delta = 1
        else:
            delta = 0
        return delta

    def update_sine(self, frequency, tt):

        f0 = frequency
        phi = 0
        sine = np.sin(2*np.pi*f0*tt*self.g.dt)
        return sine

    def update_T(self):

        self.g.T1[1:-1,1:-1,1:-1] = \
          self.m.C[1:-1,1:-1,1:-1,0,0]*self.g.u2T*(self.g.ux[1:,1:-1,1:-1] - self.g.ux[:-1,1:-1,1:-1]) \
        + self.m.C[1:-1,1:-1,1:-1,0,1]*self.g.u2T*(self.g.uy[1:-1,1:,1:-1] - self.g.uy[1:-1,:-1,1:-1]) \
        + self.m.C[1:-1,1:-1,1:-1,0,2]*self.g.u2T*(self.g.uz[1:-1,1:-1,1:] - self.g.uz[1:-1,1:-1,:-1])

        self.g.T2[1:-1,1:-1,1:-1] = \
          self.m.C[1:-1,1:-1,1:-1,1,0]*self.g.u2T*(self.g.ux[1:,1:-1,1:-1] - self.g.ux[:-1,1:-1,1:-1]) \
        + self.m.C[1:-1,1:-1,1:-1,1,1]*self.g.u2T*(self.g.uy[1:-1,1:,1:-1] - self.g.uy[1:-1,:-1,1:-1]) \
        + self.m.C[1:-1,1:-1,1:-1,1,2]*self.g.u2T*(self.g.uz[1:-1,1:-1,1:] - self.g.uz[1:-1,1:-1,:-1])

        self.g.T3[1:-1,1:-1,1:-1] = \
          self.m.C[1:-1,1:-1,1:-1,2,0]*self.g.u2T*(self.g.ux[1:,1:-1,1:-1] - self.g.ux[:-1,1:-1,1:-1]) \
        + self.m.C[1:-1,1:-1,1:-1,2,1]*self.g.u2T*(self.g.uy[1:-1,1:,1:-1] - self.g.uy[1:-1,:-1,1:-1]) \
        + self.m.C[1:-1,1:-1,1:-1,2,2]*self.g.u2T*(self.g.uz[1:-1,1:-1,1:] - self.g.uz[1:-1,1:-1,:-1])

        self.g.T4[1:-1,:,:] = self.m.C[1:-1,1:,1:,3,3]*self.g.u2T*( \
                                   (self.g.uy[1:-1,:,1:] - self.g.uy[1:-1,:,:-1]) \
                                 + (self.g.uz[1:-1,1:,:] - self.g.uz[1:-1,:-1,:]))

        self.g.T5[:,1:-1,:] = self.m.C[1:,1:-1,1:,4,4]*self.g.u2T*( \
                                   (self.g.ux[:,1:-1,1:] - self.g.ux[:,1:-1,:-1]) \
                                 + (self.g.uz[1:,1:-1,:] - self.g.uz[:-1,1:-1,:]))

        self.g.T6[:,:,1:-1] = self.m.C[1:,1:,1:-1,5,5]*self.g.u2T*( \
                                    (self.g.ux[:,1:,1:-1] - self.g.ux[:,:-1,1:-1]) \
                                  + (self.g.uy[1:,:,1:-1] - self.g.uy[:-1,:,1:-1]))

    def update_T_BC(self):

        # self.apply_T_pbc(g)
        self.apply_T_tfbc()

    def apply_T_pbc(self):

        self.g.T1[:,0,:] = self.g.T1[:,-2,:]
        self.g.T2[:,0,:] = self.g.T2[:,-2,:]
        self.g.T3[:,0,:] = self.g.T3[:,-2,:]
        # self.g.T4[:,0,:] = self.g.T4[:,-2,:]
        self.g.T5[:,0,:] = self.g.T5[:,-2,:]
        # self.g.T6[:,0,:] = self.g.T6[:,-2,:]

        # self.g.T1[:,-1,:] = self.g.T1[:,1,:]
        # self.g.T2[:,-1,:] = self.g.T2[:,1,:]
        # self.g.T3[:,-1,:] = self.g.T3[:,1,:]
        self.g.T4[:,-1,:] = self.g.T4[:,1,:]
        # self.g.T5[:,-1,:] = self.g.T5[:,1,:]
        self.g.T6[:,-1,:] = self.g.T6[:,1,:]

    def apply_T_tfbc(self):

        self.g.T1[1:-1,1:-1,0] = \
          self.m.C[1:-1,1:-1,0,0,0]*self.g.u2T*(self.g.ux[1:,1:-1,0] - self.g.ux[:-1,1:-1,0]) \
        + self.m.C[1:-1,1:-1,0,0,1]*self.g.u2T*(self.g.uy[1:-1,1:,0] - self.g.uy[1:-1,:-1,0]) \
        + self.m.C[1:-1,1:-1,0,0,2]*self.g.u2T*(self.g.uz[1:-1,1:-1,0] - 0)

        self.g.T2[1:-1,1:-1,0] = \
          self.m.C[1:-1,1:-1,0,1,0]*self.g.u2T*(self.g.ux[1:,1:-1,0] - self.g.ux[:-1,1:-1,0]) \
        + self.m.C[1:-1,1:-1,0,1,1]*self.g.u2T*(self.g.uy[1:-1,1:,0] - self.g.uy[1:-1,:-1,0]) \
        + self.m.C[1:-1,1:-1,0,1,2]*self.g.u2T*(self.g.uz[1:-1,1:-1,0] - 0)

        self.g.T3[1:-1,1:-1,0] = 0

        self.g.T4[1:-1,:,0] = self.m.C[1:-1,1:,0,3,3]*self.g.u2T*( \
                                   (self.g.uy[1:-1,:,1] - self.g.uy[1:-1,:,0]) \
                                 + (self.g.uz[1:-1,1:,0] - self.g.uz[1:-1,:-1,0]))

        self.g.T5[:,1:-1,0] = self.m.C[1:,1:-1,0,4,4]*self.g.u2T*( \
                                   (self.g.ux[:,1:-1,1] - self.g.ux[:,1:-1,0]) \
                                 + (self.g.uz[1:,1:-1,0] - self.g.uz[:-1,1:-1,0]))

        self.g.T6[:,:,0] = self.m.C[1:,1:,0,5,5]*self.g.u2T*( \
                                    (self.g.ux[:,1:,0] - self.g.ux[:,:-1,0]) \
                                  + (self.g.uy[1:,:,0] - self.g.uy[:-1,:,0]))

    def update_u(self):

        self.g.ux_new[:,1:-1,1:-1] = 2*self.g.ux[:,1:-1,1:-1] \
            - self.g.ux_old[:,1:-1,1:-1] \
            + self.g.T2u[1:,1:-1,1:-1]*( \
              (self.g.T1[1:,1:-1,1:-1] - self.g.T1[:-1,1:-1,1:-1]) \
            + (self.g.T5[:,1:-1,1:] - self.g.T5[:,1:-1,:-1]) \
            + (self.g.T6[:,1:,1:-1] - self.g.T6[:,:-1,1:-1]))

        self.g.uy_new[1:-1,:,1:-1] = 2*self.g.uy[1:-1,:,1:-1] \
            - self.g.uy_old[1:-1,:,1:-1] \
            + self.g.T2u[1:-1,1:,1:-1]*( \
              (self.g.T2[1:-1,1:,1:-1] - self.g.T2[1:-1,:-1,1:-1]) \
            + (self.g.T4[1:-1,:,1:] - self.g.T4[1:-1,:,:-1]) \
            + (self.g.T6[1:,:,1:-1] - self.g.T6[:-1,:,1:-1]))

        self.g.uz_new[1:-1,1:-1,:] = 2*self.g.uz[1:-1,1:-1,:] \
            - self.g.uz_old[1:-1,1:-1,:] \
            + self.g.T2u[1:-1,1:-1,1:]*( \
              (self.g.T3[1:-1,1:-1,1:] - self.g.T3[1:-1,1:-1,:-1]) \
            + (self.g.T4[1:-1,1:,:] - self.g.T4[1:-1,:-1,:]) \
            + (self.g.T5[1:,1:-1,:] - self.g.T5[:-1,1:-1,:]))

    def update_u_BC(self):

        # self.apply_u_pbc()
        self.apply_u_tfbc()
        self.apply_u_abc1()

    def apply_u_pbc(self):

        self.g.ux_new[:,0,:] = self.g.ux_new[:,-2,:]
        # self.g.uy_new[:,0,:] = self.g.uy_new[:,-2,:]
        self.g.uz_new[:,0,:] = self.g.uz_new[:,-2,:]

        # self.g.ux_new[:,-1,:] = self.g.ux_new[:,1,:]
        self.g.uy_new[:,-1,:] = self.g.uy_new[:,1,:]
        # self.g.uz_new[:,-1,:] = self.g.uz_new[:,1,:]

    def apply_u_tfbc(self):

        self.g.ux_new[:,1:-1,0] = 2*self.g.ux[:,1:-1,0] \
            - self.g.ux_old[:,1:-1,0] \
            + self.g.T2u[1:,1:-1,0]*( \
              (self.g.T1[1:,1:-1,0] - self.g.T1[:-1,1:-1,0]) \
            + (self.g.T5[:,1:-1,0] - 0) \
            + (self.g.T6[:,1:,0] - self.g.T6[:,:-1,0]))

        self.g.uy_new[1:-1,:,0] = 2*self.g.uy[1:-1,:,0] \
            - self.g.uy_old[1:-1,:,0] \
            + self.g.T2u[1:-1,1:,0]*( \
              (self.g.T2[1:-1,1:,0] - self.g.T2[1:-1,:-1,0]) \
            + (self.g.T4[1:-1,:,0] - 0) \
            + (self.g.T6[1:,:,0] - self.g.T6[:-1,:,0]))

        self.g.uz_new[1:-1,1:-1,0] = 2*self.g.uz[1:-1,1:-1,0] \
            - self.g.uz_old[1:-1,1:-1,0] \
            + self.g.T2u[1:-1,1:-1,0]*( \
              (self.g.T3[1:-1,1:-1,1] - self.g.T3[1:-1,1:-1,0]) \
            + (self.g.T4[1:-1,1:,0] - self.g.T4[1:-1,:-1,0]) \
            + (self.g.T5[1:,1:-1,0] - self.g.T5[:-1,1:-1,0]))

    def apply_u_abc1(self):

        cl = self.m.abc_coef_long
        ct = self.m.abc_coef_tran

        # self.g.ux_new[0,:,:] = self.g.ux[1,:,:] + cl*(self.g.ux_new[1,:,:]-self.g.ux[0,:,:])
        # self.g.uy_new[0,:,:] = self.g.uy[1,:,:] + ct*(self.g.uy_new[1,:,:]-self.g.uy[0,:,:])
        # self.g.uz_new[0,:,:] = self.g.uz[1,:,:] + ct*(self.g.uz_new[1,:,:]-self.g.uz[0,:,:])
        self.g.ux_new[-1,:,:] = self.g.ux[-2,:,:] + cl*(self.g.ux_new[-2,:,:]-self.g.ux[-1,:,:])
        self.g.uy_new[-1,:,:] = self.g.uy[-2,:,:] + ct*(self.g.uy_new[-2,:,:]-self.g.uy[-1,:,:])
        self.g.uz_new[-1,:,:] = self.g.uz[-2,:,:] + ct*(self.g.uz_new[-2,:,:]-self.g.uz[-1,:,:])

        self.g.ux_new[:,0,:] = self.g.ux[:,1,:]  + ct*(self.g.ux_new[:,1,:]-self.g.ux[:,0,:])
        self.g.uy_new[:,0,:] = self.g.uy[:,1,:]  + cl*(self.g.uy_new[:,1,:]-self.g.uy[:,0,:])
        self.g.uz_new[:,0,:] = self.g.uz[:,1,:]  + ct*(self.g.uz_new[:,1,:]-self.g.uz[:,0,:])
        self.g.ux_new[:,-1,:] = self.g.ux[:,-2,:] + ct*(self.g.ux_new[:,-2,:]-self.g.ux[:,-1,:])
        self.g.uy_new[:,-1,:] = self.g.uy[:,-2,:] + cl*(self.g.uy_new[:,-2,:]-self.g.uy[:,-1,:])
        self.g.uz_new[:,-1,:] = self.g.uz[:,-2,:] + ct*(self.g.uz_new[:,-2,:]-self.g.uz[:,-1,:])

        # self.g.ux_new[:,:,0] = self.g.ux[:,:,1] + ct*(self.g.ux_new[:,:,1]-self.g.ux[:,:,0])
        # self.g.uy_new[:,:,0] = self.g.uy[:,:,1] + ct*(self.g.uy_new[:,:,1]-self.g.uy[:,:,0])
        # self.g.uz_new[:,:,0] = self.g.uz[:,:,1] + cl*(self.g.uz_new[:,:,1]-self.g.uz[:,:,0])
        self.g.ux_new[:,:,-1] = self.g.ux[:,:,-2] + ct*(self.g.ux_new[:,:,-2]-self.g.ux[:,:,-1])
        self.g.uy_new[:,:,-1] = self.g.uy[:,:,-2] + ct*(self.g.uy_new[:,:,-2]-self.g.uy[:,:,-1])
        self.g.uz_new[:,:,-1] = self.g.uz[:,:,-2] + cl*(self.g.uz_new[:,:,-2]-self.g.uz[:,:,-1])

    def time_step(self):

        self.g.ux_temp[:,:,:] = self.g.ux
        self.g.uy_temp[:,:,:] = self.g.uy
        self.g.uz_temp[:,:,:] = self.g.uz

        self.g.ux[:,:,:] = self.g.ux_new
        self.g.uy[:,:,:] = self.g.uy_new
        self.g.uz[:,:,:] = self.g.uz_new

        self.g.ux_old[:,:,:] = self.g.ux_temp
        self.g.uy_old[:,:,:] = self.g.uy_temp
        self.g.uz_old[:,:,:] = self.g.uz_temp
