import tempfile, shutil, os
from pathlib import Path
import h5py
import threading, queue
import numpy as np

if __name__ == '__main__':
    import sys
    file = Path(__file__).resolve()
    sys.path.append(str(file.parents[1]))

from simulation import material, grid

class TestDefaults:
    properties = { "GaAs":
        {
            "p": 5307,
            "c": np.array([
                [11.88, 5.87, 5.38, 0, 0, 0],
                [5.87, 11.88, 5.38, 0, 0, 0],
                [5.87, 5.38, 11.88, 0, 0, 0],
                [0, 0, 0, 5.94, 0, 0],
                [0, 0, 0, 0, 5.94, 0],
                [0, 0, 0, 0, 0, 5.94]
            ])*1e10
        }
    }


    g = grid.Grid()
    g.init(
        size_x = 4,
        size_y = 5,
        size_z = 6
    )

    m = material.Material()
    m.init(
        grid = g,
        properties = properties
    )

    g.min_d = 1
    g.max_dx = 1
    g.max_dy = 1
    g.max_dz = 1
    g.slope = 0
    g.buildMesh()
    m.setPrimary("GaAs")
    m.setSecondary("GaAs")

class Writer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.kill = threading.Event()
        self.daemon = True

    def put(self, obj):
        if not self.is_alive():
            raise Exception("Thread not started")
        self.queue.put(obj)

    def init(self, steps, material, grid, file):
        self.hdf = h5py.File(file, mode='w')
        x, y, z, t = grid.x.size, grid.y.size, grid.z.size, steps
        self.ux = self.hdf.create_dataset("ux", (x-1,y,z,t), dtype=np.float64)
        self.uy = self.hdf.create_dataset("uy", (x,y-1,z,t), dtype=np.float64)
        self.uz = self.hdf.create_dataset("uz", (x,y,z-1,t), dtype=np.float64)
        m = self.hdf.create_dataset("density", data=material.P, dtype=np.float64)

        self.hdf.attrs["grid_x"] = grid.x
        self.hdf.attrs["grid_y"] = grid.y
        self.hdf.attrs["grid_z"] = grid.z
        self.hdf.attrs["steps"] = steps
        self.hdf.attrs["dt"] = material.dt
        #self.hdf.flush()
        # HDF FILE LEFT OPEN

    def run(self):
        while True:
            if self.kill.is_set():
                break
            try:
                g, tt = self.queue.get(block=True)
                self.ux[:,:,:,tt] = g.ux
                self.uy[:,:,:,tt] = g.uy
                self.uz[:,:,:,tt] = g.uz
            except queue.Empty:
                pass

        self.hdf.flush()
        self.hdf.close()


class BaseSolver:

    def __init__(self, logger):
        self.name = "default"
        self.description = "<p></p>"
        with tempfile.NamedTemporaryFile() as f:
            self.file = os.path.realpath(f.name)
        self.cfg = {}
        self.running = threading.Event()
        self.writer = Writer()
        self.logger = logger

    def init(self, grid, material, steps):
        self.g = grid
        self.m = material
        self.t = steps

        with self.g.lock:
            self.g.buildMesh()
            self.g.update()
        with self.m.lock:
            self.m.update()

        if self.writer.is_alive():
            self.writer.kill.set()
            self.writer.join(timeout=1)

        self.writer = Writer()
        self.writer.init(
            steps = self.t,
            file = self.file,
            grid = self.g,
            material = self.m
        )
        self.writer.start()

    def run(self, *args, **kwargs):
        try:
            signals = kwargs['signals']
        except KeyError:
            from gui.worker import WorkerSignals
            signals = WorkerSignals()

        signals.status.emit("Solver starting..")
        self.running.set()

        self.g.lock.acquire()
        self.m.lock.acquire()
        signals.status.emit("Running simulation.")
        for tt in range(self.t):
            if not self.running.is_set():
                self.logger.warning("Simulation cancelled.")
                break
            self.g.uz[0, :, 0] = self.update_ricker(tt) #applied to input face of simulation
            self.update_T()
            self.update_T_BC()
            self.update_u()
            self.update_u_BC()
            self.time_step()

            self.writer.put((self.g, tt))

            progress = ((tt+1)/self.t)*100
            if progress % 1 == 0:
                print(progress)
                signals.progress.emit(progress)

        self.g.lock.release()
        self.m.lock.release()
        self.running.clear()
        self.writer.kill.set()
        self.writer.join(timeout=1)

        signals.status.emit("Simulation finished.")

    def test(self):
        self.init(
            grid = TestDefaults.g,
            material = TestDefaults.m,
            steps = 10
        )
        self.run()

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

if __name__ == '__main__':
    import logging
    logger = logging.getLogger(__name__)
    s = BaseSolver(logger)
    s.test()
