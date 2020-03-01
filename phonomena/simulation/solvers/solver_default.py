import numpy as np
from gui.worker import WorkerSignals
from time import sleep

from simulation.solvers import test_defaults

class Solver:

    def __init__(self):
        self.signals = WorkerSignals()
        self.name = "default"
        self.description = "<p></p>"

    def test(self):
        self.init(
            grid = test_defaults.g,
            material = test_defaults.m
        )
        self.run(
            steps = 10,
            signals = WorkerSignals())

    def init(self, grid, material):
        self.g = grid
        self.m = material
        self.g.buildMesh()
        self.g.update()
        self.m.update()

    def run(self, *args, **kwargs):
        steps = kwargs['steps']
        self.signals = kwargs['signals']

        self.signals.status.emit("Solver starting..")

        for tt in range(steps):
            self.g.uz[0, :, 0] = self.update_ricker(tt) #applied to input face of simulation
            self.update_T()
            self.update_T_BC()
            self.update_u()
            self.update_u_BC()
            self.time_step()
            progress = tt/steps*100+1
            if progress % 1 == 0:
                self.signals.progress.emit(progress)

    def update_ricker(self, tt):

        # define constants for ricker wave
        ppw = 20 # points per wavelength
        source_delay = 0

        # create ricker wave
        arg = (np.pi*((self.m.c_max*tt - source_delay)/ppw - 1.0)) ** 2
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
          self.m.C[1:-1,1:-1,1:-1,0,0]*(self.g.ux[1:,1:-1,1:-1] - self.g.ux[:-1,1:-1,1:-1]) \
        / self.g.sdx \
        + self.m.C[1:-1,1:-1,1:-1,0,1]*(self.g.uy[1:-1,1:,1:-1] - self.g.uy[1:-1,:-1,1:-1]) \
        / self.g.sdy \
        + self.m.C[1:-1,1:-1,1:-1,0,2]*(self.g.uz[1:-1,1:-1,1:] - self.g.uz[1:-1,1:-1,:-1]) \
        / self.g.sdz


        self.g.T2[1:-1,1:-1,1:-1] = \
          self.m.C[1:-1,1:-1,1:-1,1,0]*(self.g.ux[1:,1:-1,1:-1] - self.g.ux[:-1,1:-1,1:-1]) \
        / self.g.sdx \
        + self.m.C[1:-1,1:-1,1:-1,1,1]*(self.g.uy[1:-1,1:,1:-1] - self.g.uy[1:-1,:-1,1:-1]) \
        / self.g.sdy \
        + self.m.C[1:-1,1:-1,1:-1,1,2]*(self.g.uz[1:-1,1:-1,1:] - self.g.uz[1:-1,1:-1,:-1]) \
        / self.g.sdz

        self.g.T3[1:-1,1:-1,1:-1] = \
            self.m.C[1:-1,1:-1,1:-1,2,0]*(self.g.ux[1:,1:-1,1:-1] - self.g.ux[:-1,1:-1,1:-1]) \
            / self.g.sdx \
            + self.m.C[1:-1,1:-1,1:-1,2,1]*(self.g.uy[1:-1,1:,1:-1] - self.g.uy[1:-1,:-1,1:-1]) \
            / self.g.sdy \
            + self.m.C[1:-1,1:-1,1:-1,2,2]*(self.g.uz[1:-1,1:-1,1:] - self.g.uz[1:-1,1:-1,:-1]) \
            / self.g.sdz

        self.g.T4[1:-1,:,:] = self.m.C[1:-1,1:,1:,3,3]*( \
            (self.g.uy[1:-1,:,1:] - self.g.uy[1:-1,:,:-1]) \
            / self.g.fdz \
            + (self.g.uz[1:-1,1:,:] - self.g.uz[1:-1,:-1,:]) \
            / self.g.fdy
        )

        self.g.T5[:,1:-1,:] = self.m.C[1:,1:-1,1:,4,4]*( \
            (self.g.ux[:,1:-1,1:] - self.g.ux[:,1:-1,:-1]) \
            / self.g.fdz \
            + (self.g.uz[1:,1:-1,:] - self.g.uz[:-1,1:-1,:])
            / self.g.fdx
        )

        self.g.T6[:,:,1:-1] = self.m.C[1:,1:,1:-1,5,5]*( \
            (self.g.ux[:,1:,1:-1] - self.g.ux[:,:-1,1:-1]) \
            / self.g.fdy \
            + (self.g.uy[1:,:,1:-1] - self.g.uy[:-1,:,1:-1]) \
            / self.g.fdx
        )

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
            self.m.C[1:-1,1:-1,0,0,0]*(self.g.ux[1:,1:-1,0] - self.g.ux[:-1,1:-1,0]) / self.g.sdx[0,:,:] \
            + self.m.C[1:-1,1:-1,0,0,1]*(self.g.uy[1:-1,1:,0] - self.g.uy[1:-1,:-1,0]) / self.g.sdy[:,0,:] \
            + self.m.C[1:-1,1:-1,0,0,2]*(self.g.uz[1:-1,1:-1,0] - 0) / self.g.sdz[:,:,0]

        self.g.T2[1:-1,1:-1,0] = \
            self.m.C[1:-1,1:-1,0,1,0]*(self.g.ux[1:,1:-1,0] - self.g.ux[:-1,1:-1,0]) / self.g.sdx[0,:,:] \
            + self.m.C[1:-1,1:-1,0,1,1]*(self.g.uy[1:-1,1:,0] - self.g.uy[1:-1,:-1,0]) / self.g.sdy[:,0,:] \
            + self.m.C[1:-1,1:-1,0,1,2]*(self.g.uz[1:-1,1:-1,0] - 0) / self.g.sdz[:,:,0]

        self.g.T3[1:-1,1:-1,0] = 0

        self.g.T4[1:-1,:,0] = \
            self.m.C[1:-1,1:,0,3,3] \
            * ((self.g.uy[1:-1,:,1] - self.g.uy[1:-1,:,0]) / self.g.fdy[:,0,:] \
            + (self.g.uz[1:-1,1:,0] - self.g.uz[1:-1,:-1,0]) / self.g.fdz[:,:,0])

        self.g.T5[:,1:-1,0] = \
            self.m.C[1:,1:-1,0,4,4] \
            * ((self.g.ux[:,1:-1,1] - self.g.ux[:,1:-1,0]) / self.g.fdx[0,:,:] \
            + (self.g.uz[1:,1:-1,0] - self.g.uz[:-1,1:-1,0]) / self.g.fdz[:,:,0])

        self.g.T6[:,:,0] = \
            self.m.C[1:,1:,0,5,5] \
            * ((self.g.ux[:,1:,0] - self.g.ux[:,:-1,0]) / self.g.fdx[0,:,:] \
            + (self.g.uy[1:,:,0] - self.g.uy[:-1,:,0]) / self.g.fdz[:,:,0])

    def update_u(self):

        self.g.ux_new[:,1:-1,1:-1] = 2*self.g.ux[:,1:-1,1:-1] \
            - self.g.ux_old[:,1:-1,1:-1] \
            + (self.m.dt**2/self.m.P[1:,1:-1,1:-1]) \
            * ((self.g.T1[1:,1:-1,1:-1] - self.g.T1[:-1,1:-1,1:-1]) / self.g.fdx \
                + (self.g.T6[:,1:,1:-1] - self.g.T6[:,:-1,1:-1]) / self.g.sdy \
                + (self.g.T5[:,1:-1,1:] - self.g.T5[:,1:-1,:-1]) / self.g.sdz \
            )

        self.g.uy_new[1:-1,:,1:-1] = 2*self.g.uy[1:-1,:,1:-1] \
            - self.g.uy_old[1:-1,:,1:-1] \
            + (self.m.dt**2/self.m.P[1:-1,1:,1:-1]) \
            * ((self.g.T6[1:,:,1:-1] - self.g.T6[:-1,:,1:-1]) / self.g.sdx \
                + (self.g.T2[1:-1,1:,1:-1] - self.g.T2[1:-1,:-1,1:-1]) / self.g.fdy \
                + (self.g.T4[1:-1,:,1:] - self.g.T4[1:-1,:,:-1]) / self.g.sdz \
            )

        self.g.uz_new[1:-1,1:-1,:] = 2*self.g.uz[1:-1,1:-1,:] \
            - self.g.uz_old[1:-1,1:-1,:] \
            + (self.m.dt**2/self.m.P[1:-1,1:-1,1:]) \
            * ((self.g.T5[1:,1:-1,:] - self.g.T5[:-1,1:-1,:]) / self.g.sdx \
                + (self.g.T4[1:-1,1:,:] - self.g.T4[1:-1,:-1,:]) / self.g.sdy \
                + (self.g.T3[1:-1,1:-1,1:] - self.g.T3[1:-1,1:-1,:-1]) / self.g.fdz \
            )

    def update_u_BC(self):

        # self.apply_u_pbc()
        self.apply_u_tfbc()
        self.apply_u_abc()

    def apply_u_pbc(self):

        self.g.ux_new[:,0,:] = self.g.ux_new[:,-2,:]
        # self.g.uy_new[:,0,:] = self.g.uy_new[:,-2,:]
        self.g.uz_new[:,0,:] = self.g.uz_new[:,-2,:]

        # self.g.ux_new[:,-1,:] = self.g.ux_new[:,1,:]
        self.g.uy_new[:,-1,:] = self.g.uy_new[:,1,:]
        # self.g.uz_new[:,-1,:] = self.g.uz_new[:,1,:]

    def apply_u_tfbc(self):
        # affects z = 0 index only

        self.g.ux_new[:,1:-1,0] = 2*self.g.ux[:,1:-1,0] \
            - self.g.ux_old[:,1:-1,0] \
            + (self.m.dt**2/self.m.P[1:,1:-1,0]) \
            * ((self.g.T1[1:,1:-1,0] - self.g.T1[:-1,1:-1,0]) / self.g.fdx[0,:,:] \
                + (self.g.T6[:,1:,0] - self.g.T6[:,:-1,0]) / self.g.sdy[:,0,:] \
                + (self.g.T5[:,1:-1,0] - 0) / self.g.sdz[:,:,0] \
            )

        self.g.uy_new[1:-1,:,0] = 2*self.g.uy[1:-1,:,0] \
            - self.g.uy_old[1:-1,:,0] \
            + (self.m.dt**2/self.m.P[1:-1,1:,0]) \
            * ((self.g.T6[1:,:,0] - self.g.T6[:-1,:,0]) / self.g.sdx[0,:,:] \
                + (self.g.T2[1:-1,1:,0] - self.g.T2[1:-1,:-1,0]) / self.g.fdy[:,0,:] \
                + (self.g.T4[1:-1,:,0] - 0) / self.g.sdz[:,:,0] \
            )

        self.g.uz_new[1:-1,1:-1,0] = 2*self.g.uz[1:-1,1:-1,0] \
            - self.g.uz_old[1:-1,1:-1,0] \
            + (self.m.dt**2/self.m.P[1:-1,1:-1,0]) \
            * ((self.g.T5[1:,1:-1,0] - self.g.T5[:-1,1:-1,0]) / self.g.sdx[0,:,:] \
                + (self.g.T4[1:-1,1:,0] - self.g.T4[1:-1,:-1,0]) / self.g.sdy[:,0,:] \
                + self.g.T3[1:-1,1:-1,1] - self.g.T3[1:-1,1:-1,0] / self.g.fdz[:,:,0] \
            )

    def apply_u_abc(self):

        c11 = self.m.C[0,0,0,0,0]
        c44 = self.m.C[0,0,0,3,3]
        vl = np.sqrt(c11/self.m.P[0,0,0]) # parallel
        vt = np.sqrt(c44/self.m.P[0,0,0]) # transverse

        ctx = ((vt*self.m.dt-self.g.fdx)/(vt*self.m.dt+self.g.fdx))[:,0,0] # shifted transverse constant
        clx = ((vl*self.m.dt-self.g.sdx)/(vl*self.m.dt+self.g.sdx))[:,0,0] # shifted parallel constant

        cty = ((vt*self.m.dt-self.g.fdy)/(vt*self.m.dt+self.g.fdy))[0,:,0]
        cly = ((vl*self.m.dt-self.g.sdy)/(vl*self.m.dt+self.g.sdy))[0,:,0]

        ctz = ((vt*self.m.dt-self.g.fdz)/(vt*self.m.dt+self.g.fdz))[0,0,:]
        clz = ((vl*self.m.dt-self.g.sdz)/(vl*self.m.dt+self.g.sdz))[0,0,:]

        # YZ face
        self.g.ux_new[-1,:,:] = self.g.ux[-2,:,:] + clx[-1]*(self.g.ux_new[-2,:,:]-self.g.ux[-1,:,:])
        self.g.uy_new[-1,:,:] = self.g.uy[-2,:,:] + ctx[-1]*(self.g.uy_new[-2,:,:]-self.g.uy[-1,:,:])
        self.g.uz_new[-1,:,:] = self.g.uz[-2,:,:] + ctx[-1]*(self.g.uz_new[-2,:,:]-self.g.uz[-1,:,:])

        self.g.ux_new[:,0,:] = self.g.ux[:,1,:] + cty[0]*(self.g.ux_new[:,1,:]-self.g.ux[:,0,:])
        self.g.uy_new[:,0,:] = self.g.uy[:,1,:] + cly[0]*(self.g.uy_new[:,1,:]-self.g.uy[:,0,:])
        self.g.uz_new[:,0,:] = self.g.uz[:,1,:] + cty[0]*(self.g.uz_new[:,1,:]-self.g.uz[:,0,:])

        self.g.ux_new[:,-1,:] = self.g.ux[:,-2,:] + cty[-1]*(self.g.ux_new[:,-2,:]-self.g.ux[:,-1,:])
        self.g.uy_new[:,-1,:] = self.g.uy[:,-2,:] + cly[-1]*(self.g.uy_new[:,-2,:]-self.g.uy[:,-1,:])
        self.g.uz_new[:,-1,:] = self.g.uz[:,-2,:] + cty[-1]*(self.g.uz_new[:,-2,:]-self.g.uz[:,-1,:])

        self.g.ux_new[:,:,-1] = self.g.ux[:,:,-2] + ctz[-1]*(self.g.ux_new[:,:,-2]-self.g.ux[:,:,-1])
        self.g.uy_new[:,:,-1] = self.g.uy[:,:,-2] + ctz[-1]*(self.g.uy_new[:,:,-2]-self.g.uy[:,:,-1])
        self.g.uz_new[:,:,-1] = self.g.uz[:,:,-2] + clz[-1]*(self.g.uz_new[:,:,-2]-self.g.uz[:,:,-1])

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
