from numba import njit

from simulation import base_solver

import logging
logger = logging.getLogger(__name__)

cfg = {
    "cache": True,
    "fastmath": True
}

class Solver(base_solver.BaseSolver):

    def __init__(self):
        super().__init__(logger)
        self.name = "numba"
        self.description = "<p></p>"
        global cfg
        self.cfg = {**self.cfg, **cfg}
        cfg = self.cfg

    def run(self, *args, **kwargs):
        global cfg
        if cfg != self.cfg:
            cfg = self.cfg
            self.logger.debug("Recompiling numba funcs")
            self.recompile()
        super().run(*args, **kwargs)

    def recompile(self):
        update_T.recompile()
        update_T_tfbc.recompile()

    def update_T(self):

        u = (self.g.ux, self.g.uy, self.g.uz)
        sd = (self.g.sdx, self.g.sdy, self.g.sdz)
        fd = (self.g.fdx, self.g.fdy, self.g.fdz)

        T1, T2, T3, T4, T5, T6 = update_T(self.m.C, u, sd, fd)
        self.g.T1[1:-1,1:-1,1:-1] = T1
        self.g.T2[1:-1,1:-1,1:-1] = T2
        self.g.T3[1:-1,1:-1,1:-1] = T3
        self.g.T4[1:-1,:,:] = T4
        self.g.T5[:,1:-1,:] = T5
        self.g.T6[:,:,1:-1] = T6

    def apply_T_tfbc(self):

        u = (self.g.ux, self.g.uy, self.g.uz)
        sd = (self.g.sdx, self.g.sdy, self.g.sdz)
        fd = (self.g.fdx, self.g.fdy, self.g.fdz)

        T1, T2, T3, T4, T5, T6 = update_T_tfbc(self.m.C, u, sd, fd)

        self.g.T1[1:-1,1:-1,0] = T1
        self.g.T2[1:-1,1:-1,0] = T2
        self.g.T3[1:-1,1:-1,0] = T3
        self.g.T4[1:-1,:,0] = T4
        self.g.T5[:,1:-1,0] = T5
        self.g.T6[:,:,0] = T6


@njit(cache=cfg['cache'], fastmath=cfg['fastmath'])
def update_T(C, u, sd, fd):
    ux, uy, uz = u
    sdx, sdy, sdz = sd
    fdx, fdy, fdz = fd

    T1 = \
      C[1:-1,1:-1,1:-1,0,0]*(ux[1:,1:-1,1:-1] - ux[:-1,1:-1,1:-1]) \
    / sdx \
    + C[1:-1,1:-1,1:-1,0,1]*(uy[1:-1,1:,1:-1] - uy[1:-1,:-1,1:-1]) \
    / sdy \
    + C[1:-1,1:-1,1:-1,0,2]*(uz[1:-1,1:-1,1:] - uz[1:-1,1:-1,:-1]) \
    / sdz

    T2 = \
      C[1:-1,1:-1,1:-1,1,0]*(ux[1:,1:-1,1:-1] - ux[:-1,1:-1,1:-1]) \
    / sdx \
    + C[1:-1,1:-1,1:-1,1,1]*(uy[1:-1,1:,1:-1] - uy[1:-1,:-1,1:-1]) \
    / sdy \
    + C[1:-1,1:-1,1:-1,1,2]*(uz[1:-1,1:-1,1:] - uz[1:-1,1:-1,:-1]) \
    / sdz

    T3 = C[1:-1,1:-1,1:-1,2,0]*(ux[1:,1:-1,1:-1] - ux[:-1,1:-1,1:-1]) \
        / sdx \
        + C[1:-1,1:-1,1:-1,2,1]*(uy[1:-1,1:,1:-1] - uy[1:-1,:-1,1:-1]) \
        / sdy \
        + C[1:-1,1:-1,1:-1,2,2]*(uz[1:-1,1:-1,1:] - uz[1:-1,1:-1,:-1]) \
        / sdz

    T4 = C[1:-1,1:,1:,3,3]*( \
        (uy[1:-1,:,1:] - uy[1:-1,:,:-1]) \
        / fdz \
        + (uz[1:-1,1:,:] - uz[1:-1,:-1,:]) \
        / fdy
    )

    T5 = C[1:,1:-1,1:,4,4]*( \
        (ux[:,1:-1,1:] - ux[:,1:-1,:-1]) \
        / fdz \
        + (uz[1:,1:-1,:] - uz[:-1,1:-1,:])
        / fdx
    )

    T6 = C[1:,1:,1:-1,5,5]*( \
        (ux[:,1:,1:-1] - ux[:,:-1,1:-1]) \
        / fdy \
        + (uy[1:,:,1:-1] - uy[:-1,:,1:-1]) \
        / fdx
    )
    return T1,T2,T3,T4,T5,T6

@njit(cache=cfg['cache'], fastmath=cfg['fastmath'])
def update_T_tfbc(C, u, fd, sd):
    ux, uy, uz = u
    fdx, fdy, fdz = fd
    sdx, sdy, sdz = sd

    T1 = C[1:-1,1:-1,0,0,0]*(ux[1:,1:-1,0] - ux[:-1,1:-1,0]) / sdx[0,:,:] \
        + C[1:-1,1:-1,0,0,1]*(uy[1:-1,1:,0] - uy[1:-1,:-1,0]) / sdy[:,0,:] \
        + C[1:-1,1:-1,0,0,2]*(uz[1:-1,1:-1,0] - 0) / sdz[:,:,0]

    T2 = C[1:-1,1:-1,0,1,0]*(ux[1:,1:-1,0] - ux[:-1,1:-1,0]) / sdx[0,:,:] \
        + C[1:-1,1:-1,0,1,1]*(uy[1:-1,1:,0] - uy[1:-1,:-1,0]) / sdy[:,0,:] \
        + C[1:-1,1:-1,0,1,2]*(uz[1:-1,1:-1,0] - 0) / sdz[:,:,0]

    T3 = 0

    T4 = C[1:-1,1:,0,3,3] \
        * ((uy[1:-1,:,1] - uy[1:-1,:,0]) / fdy[:,0,:] \
        + (uz[1:-1,1:,0] - uz[1:-1,:-1,0]) / fdz[:,:,0])

    T5 = C[1:,1:-1,0,4,4] \
        * ((ux[:,1:-1,1] - ux[:,1:-1,0]) / fdx[0,:,:] \
        + (uz[1:,1:-1,0] - uz[:-1,1:-1,0]) / fdz[:,:,0])

    T6 = C[1:,1:,0,5,5] \
        * ((ux[:,1:,0] - ux[:,:-1,0]) / fdx[0,:,:] \
        + (uy[1:,:,0] - uy[:-1,:,0]) / fdz[:,:,0])

    return T1,T2,T3,T4,T5,T6
