import tempfile, shutil, os, sys
from pathlib import Path
import h5py as h5
import threading, queue
import numpy as np
from time import time
import math as m
import copy
import json
import multiprocessing as mp

import logging
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    import sys
    file = Path(__file__).resolve()
    sys.path.append(str(file.parents[1]))

from simulation import material, grid
from gui.worker import WorkerSignals

#https://support.hdfgroup.org/HDF5/doc/RM/H5P/H5Pset_cache.htm
#RDCC_NSLOTS = np.array((521, 1009, 2003, 3001, 4001, 5003, 6007, 7001)) # Should be prime number for best performance

DTYPE = np.float64

class TestDefaults:
    '''
    Contains minimal test setup for running tests of BaseSolver objects
    Also includes material proprties for gallium arsenside.
    Other materials can be added to and improted using data.json
    '''
    properties = { "GaAs":
        {
            "name": "Gallium Arsenide",
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

class Writer:
    '''
    Writes standardized HDF files for simulation results
    After being started using start(), grid and timestep data can be added using
    Writer.put((grid, tt)) where grid and tt are inside a tuple.
    Once the simulation is finished the thread can be killed using Writer.kill.set()
    The HDF file will be flushed to disk on thread exit
    '''
    def __init__(self, mode='thread'):
        super().__init__()
        assert mode in ['thread', 'process']
        self.queue = {'process':mp.JoinableQueue, 'thread':queue.Queue}[mode]()
        self.daemon = True
        self.mode = {'process':mp.Process, 'thread':threading.Thread}[mode]
        self.process = self.mode()
        self.file = None

    def join(self, *args, **kwargs):
        self.process.join(*args, **kwargs)
        if self.process.is_alive():
            raise mp.TimeoutError()

    def is_alive(self, *args, **kwargs):
        return self.process.is_alive(*args, **kwargs)

    def put(self, *args, **kwargs):
        if not self.process.is_alive():
            raise Exception("Process not started")
        self.queue.put(*args, **kwargs)

    def notify_finished(self):
        self.queue.put(None)

    def init(self, steps, material, grid, cfg, file):
        '''
        Sets up the HDF file in a standard format.
        The HDF file will be left open until thread exit. Do not reopen until thread has exited
        '''
        x, y, z, t = grid.x.size, grid.y.size, grid.z.size, steps
        logger.info("Writing HDF to file {}".format(file))
        self.file = file
        with h5.File(file, mode='w') as hdf:
            self.ux = hdf.create_dataset("ux", (x-1,y,z,t), chunks=(x-1,y,z,1), dtype=DTYPE)
            self.uy = hdf.create_dataset("uy", (x,y-1,z,t), chunks=(x,y-1,z,1), dtype=DTYPE)
            self.uz = hdf.create_dataset("uz", (x,y,z-1,t), chunks=(x,y,z-1,1), dtype=DTYPE)
            hdf.create_dataset("density", data=material.P, chunks=material.P.shape, dtype=DTYPE)
            hdf.create_dataset("elasticity", data=material.C, chunks=material.C.shape, dtype=DTYPE)

            hdf.attrs["x"] = grid.x
            hdf.attrs["y"] = grid.y
            hdf.attrs["z"] = grid.z
            hdf.attrs["sdx"] = grid.sdx
            hdf.attrs["sdy"] = grid.sdy
            hdf.attrs["sdz"] = grid.sdz
            hdf.attrs["fdx"] = grid.fdx
            hdf.attrs["fdy"] = grid.fdy
            hdf.attrs["fd`z"] = grid.fdz
            hdf.attrs["steps"] = steps
            hdf.attrs["dt"] = material.dt
            hdf.attrs["prim_material"] = material.primary['name']
            hdf.attrs["sec_material"] = material.secondary['name']
            hdf.attrs["solver_cfg"] = json.dumps(cfg)

    @staticmethod
    def run(file, queue_obj):
        '''
        Main loop started using Writer.start()
        '''

        hdf = h5.File(file, mode='r+')
        ux = hdf.get('ux')
        uy = hdf.get('uy')
        uz = hdf.get('uz')
        print('writer process starting.')
        sys.stdout.flush()
        while True:
            obj = queue_obj.get(timeout=2*60)
            if obj == None:
                break
            else:
                g, tt = obj
                ux[:,:,:,tt] = g.ux
                uy[:,:,:,tt] = g.uy
                uz[:,:,:,tt] = g.uz
                #hdf.flush()

        hdf.close()
        print('writer process closing.')
        sys.stdout.flush()

    def start(self):
        if self.file == None:
            raise Exception("Must run init before start.")
        assert Path(self.file).exists()
        logger.info("Starting writer in {} mode.".format(self.mode))
        self.process = self.mode(target=self.run, args=(self.file, self.queue))
        self.process.daemon = self.daemon
        self.process.start()


class BaseSolver:
    '''
    Acts as a standardized class to be inherited and modified by each custom Solver.
    Each solver run requires synchronization of simulation parameters using init()
    followed by starting the long-running process run().
    '''
    def __init__(self, logger):
        '''
        '''
        self.name = "default"
        self.description = '''
            <p>Base Solver. This string should be overwritten by the child class</p>'''
        with tempfile.NamedTemporaryFile() as f:
            self.file = os.path.realpath(f.name)
        #self.file = r'C:\Users\mattd\Desktop\test.hdf'
        self.running = threading.Event()
        self.writer = Writer()
        self.logger = logger
        self.cfg = {'wave': 'ricker',
                    'wave_args': {'f': 100},
                    'write_mode': 'process'}

    def init(self, grid, material, steps):
        '''
        Run prior to each simulation.
        Used to prepare the writer and update simulaton paramters
        '''
        self.g = copy.deepcopy(grid)
        self.m = copy.deepcopy(material)
        self.t = copy.deepcopy(steps)

        logger.info("Initializing {} with settings: {}".format(__name__, self.cfg))

        self.g.buildMesh()
        self.g.update()
        self.m.update()

        if self.cfg['write_mode'] != 'off':
            if self.writer.is_alive():
                self.writer.notify_finished()
                self.writer.join(timeout=1)

            self.writer = Writer(self.cfg['write_mode'])
            self.writer.init(
                steps = self.t,
                file = self.file,
                grid = self.g,
                cfg = self.cfg,
                material = self.m
            )
            self.writer.start()

    def run(self, *args, **kwargs):
        '''
        '''

        default = {'signals': WorkerSignals()}
        kwargs = {**default, **kwargs}
        signals = kwargs['signals']

        wave_fn = {'sin': self.update_sin,
                   'ricker': self.update_ricker}[self.cfg['wave']]

        signals.status.emit("Solver starting..")
        self.running.set()

        signals.status.emit("Running simulation.")
        stime = time()
        logger.debug("solver loop starting...")

        progress = 0
        signals.progress.emit(0)

        for tt in range(self.t):
            if not self.running.is_set():
                self.logger.warning("Simulation cancelled.")
                break

            # apply wave to input face of simulation
            self.g.uz[0, :, 0] = wave_fn(tt = tt, **self.cfg['wave_args'])
            self.update_T()
            self.update_T_BC()
            self.update_u()
            self.update_u_BC()
            self.time_step()

            if self.cfg['write_mode'] != 'off':
                cache = (self.g.freezeData(), tt)
                self.writer.put(cache)

            if progress < 99:
                progress = min(99, int(((tt+1)/self.t)*100))
                if progress % 1 == 0:
                    #print(progress)
                    signals.progress.emit(progress)

        # Cleanup
        logger.debug("solver loop ended.")
        self.running.clear()
        if self.cfg['write_mode'] != 'off':
            self.writer.notify_finished()
            t1 = time()
            self.writer.join(timeout=5*60)
            t2 = time()-t1
            logger.debug("Waited {:.4f}s for writer to end.".format(t2))

        etime = time()-stime
        signals.status.emit("Simulation finished in {:.2f}s.".format(etime))
        signals.progress.emit(100)

    def cancel(self):
        if self.running.is_set():
            self.running.clear()

    def test(self):
        self.init(
            grid = TestDefaults.g,
            material = TestDefaults.m,
            steps = 10
        )
        self.run()

    def update_sin(self, tt, f, **kwargs):
        ''' f: frequency in Hz
        **kwargs: accepts additional arguments intended for other wave functions'''

        wave = np.sin(2*np.pi*f*tt*self.m.dt)
        return wave

    def update_ricker(self, tt, f, source_delay=0, **kwargs):
        ''' Updates ricker wave_fn
         ppw: points per wavelength
         fm: peak frequency
         source_delay: phase shift (s)
         **kwargs: accepts additional arguments intended for other wave functions'''

         # Ricker wavelet equation is here https://wiki.seg.org/wiki/Dictionary:Ricker_wavelet

        arg = (np.pi*f*(self.m.dt*tt - source_delay)) ** 2
        ricker = (1 - 2 * arg) * np.exp(-arg)
        return ricker

    def update_delta(self, tt):

        source_delay = 0
        if tt == source_delay:
            delta = 1
        else:
            delta = 0
        return delta

    def update_T(self):
        '''
        Update each component of the stress tensor
        Called from run(), can be overwritten by child class
        '''

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
        '''
        Update stress tensor using boundary conditions
        TODO: Add Bloch periodic boundary conditions
        '''

        # self.apply_T_pbc(g)
        self.apply_T_tfbc()

    def apply_T_pbc(self):
        '''
        ARCHIVED: Not currently used. To be updated for Bloch periodic BC
        '''

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
        '''
        Update stress tensor using traction free BC
        Called from apply_T_BC(), can be overwritten by child class
        '''

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
        '''
        Update displacement vectors based on stress tensor
        Called from run(), can be overwritten by child class
        '''

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
        '''
        Update displacement vectors using boundary conditions
        Called from run()
        TODO: Add Bloch periodic boundary conditions
        '''
        # self.apply_u_pbc()
        self.apply_u_tfbc()
        self.apply_u_abc()

    def apply_u_pbc(self):
        '''
        ARCHIVED: Not in use. To be updated for Bloch peridoic BC
        '''

        self.g.ux_new[:,0,:] = self.g.ux_new[:,-2,:]
        # self.g.uy_new[:,0,:] = self.g.uy_new[:,-2,:]
        self.g.uz_new[:,0,:] = self.g.uz_new[:,-2,:]

        # self.g.ux_new[:,-1,:] = self.g.ux_new[:,1,:]
        self.g.uy_new[:,-1,:] = self.g.uy_new[:,1,:]
        # self.g.uz_new[:,-1,:] = self.g.uz_new[:,1,:]

    def apply_u_tfbc(self):
        '''
        Update displacement vectors using traction free BC
        Called from update_u_BC, can be overwritten by child class
        '''

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
        '''
        Update displacement vectors using absorbing BC
        Called from update_u_BC, can be overwritten by child class
        '''

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
        '''
        Update the time step, shift displacement matrices
        '''

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
