import numpy as np
import ctypes
import multiprocessing as mp
import sys
import time

from simulation import base_solver

import logging
logger = logging.getLogger(__name__)

cfg = {}

def matrix_memmap(matrix, dtype=ctypes.c_double):
    return (mp.Array(dtype, matrix.reshape(matrix.size)), matrix.shape)

def matrix_unmap(memmap, shape, dtype=np.float64):
    m = np.frombuffer(memmap.get_obj(), dtype=dtype)
    m.shape = shape
    return m

def value_memmap(value, dtype=ctypes.c_double):
    return mp.Value(dtype, value)

def value_unmap(memmap):
    return memmap.value

def worker(i, q, bundle):
    print("worker {} started".format(i))
    sys.stdout.flush()
    for key, value in bundle.items():
        if type(bundle[key]) == tuple:
            bundle[key] = matrix_unmap(*bundle[key])

    while True:
        fn = q.get()
        fn(bundle)
        q.task_done()
    print("worker {} started".format(i))
    sys.stdout.flush()

class Solver(base_solver.BaseSolver):

    def __init__(self):
        super().__init__(logger)

        self.name = "multiprocess"
        self.description = "<p></p>"
        self.cfg = {**cfg, **self.cfg}

    def init(self, *args, **kwargs):
        super().init(*args, **kwargs)

        self.worker_queue = mp.JoinableQueue()
        self.workers = []
        self.bundle = self.pack()

        num_workers = mp.cpu_count()
        for i in range(num_workers):
            self.workers.append(
                mp.Process(target=worker,
                        args=(i,
                              self.worker_queue,
                              self.bundle)))
            self.workers[i].daemon = True
            self.workers[i].start()

    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        for w in self.workers:
            w.terminate()

    def pack(self):
        b = dict()
        # Shared memory
        b['T1'] = matrix_memmap(self.g.T1)
        b['T2'] = matrix_memmap(self.g.T2)
        b['T3'] = matrix_memmap(self.g.T3)
        b['T4'] = matrix_memmap(self.g.T4)
        b['T5'] = matrix_memmap(self.g.T5)
        b['T6'] = matrix_memmap(self.g.T6)

        b['ux'] = matrix_memmap(self.g.ux)
        b['uy'] = matrix_memmap(self.g.uy)
        b['uz'] = matrix_memmap(self.g.uz)

        # Read only
        b['sdx'] = self.g.sdx
        b['sdy'] = self.g.sdy
        b['sdz'] = self.g.sdz
        b['fdx'] = self.g.fdx
        b['fdy'] = self.g.fdy
        b['fdz'] = self.g.fdz
        b['C'] = self.m.C
        return b

    def unpack(self):
        self.g.T1 = matrix_unmap(*self.bundle['T1'])
        self.g.T2 = matrix_unmap(*self.bundle['T2'])
        self.g.T3 = matrix_unmap(*self.bundle['T3'])
        self.g.T4 = matrix_unmap(*self.bundle['T4'])
        self.g.T5 = matrix_unmap(*self.bundle['T5'])
        self.g.T6 = matrix_unmap(*self.bundle['T6'])

        self.g.ux = matrix_unmap(*self.bundle['ux'])
        self.g.uy = matrix_unmap(*self.bundle['uy'])
        self.g.uz = matrix_unmap(*self.bundle['uz'])

    def update_T(self):
        self.worker_queue.put(update_T1)
        self.worker_queue.put(update_T2)
        self.worker_queue.put(update_T3)
        self.worker_queue.put(update_T4)
        self.worker_queue.put(update_T5)
        self.worker_queue.put(update_T6)
        self.worker_queue.join()
        self.unpack()

    def update_T_tfbc(self):
        self.worker_queue.put(update_T1_tfbc)
        self.worker_queue.put(update_T2_tfbc)
        self.worker_queue.put(update_T4_tfbc)
        self.worker_queue.put(update_T5_tfbc)
        self.worker_queue.put(update_T6_tfbc)
        self.g.T3[1:-1,1:-1,0] = 0
        self.worker_queue.join()
        self.unpack()

def update_T1(b):
    b['T1'][1:-1,1:-1,1:-1] = \
      b['C'][1:-1,1:-1,1:-1,0,0]*(b['ux'][1:,1:-1,1:-1] - b['ux'][:-1,1:-1,1:-1]) \
    / b['sdx'] \
    + b['C'][1:-1,1:-1,1:-1,0,1]*(b['uy'][1:-1,1:,1:-1] - b['uy'][1:-1,:-1,1:-1]) \
    / b['sdy'] \
    + b['C'][1:-1,1:-1,1:-1,0,2]*(b['uz'][1:-1,1:-1,1:] - b['uz'][1:-1,1:-1,:-1]) \
    / b['sdz']

def update_T2(b):
    b['T1'][1:-1,1:-1,1:-1] = \
      b['C'][1:-1,1:-1,1:-1,1,0]*(b['ux'][1:,1:-1,1:-1] - b['ux'][:-1,1:-1,1:-1]) \
    / b['sdx'] \
    + b['C'][1:-1,1:-1,1:-1,1,1]*(b['uy'][1:-1,1:,1:-1] - b['uy'][1:-1,:-1,1:-1]) \
    / b['sdy'] \
    + b['C'][1:-1,1:-1,1:-1,1,2]*(b['uz'][1:-1,1:-1,1:] - b['uz'][1:-1,1:-1,:-1]) \
    / b['sdz']

def update_T3(b):
    b['T3'][1:-1,1:-1,1:-1] = \
        b['C'][1:-1,1:-1,1:-1,2,0]*(b['ux'][1:,1:-1,1:-1] - b['ux'][:-1,1:-1,1:-1]) \
        / b['sdx'] \
        + b['C'][1:-1,1:-1,1:-1,2,1]*(b['uy'][1:-1,1:,1:-1] - b['uy'][1:-1,:-1,1:-1]) \
        / b['sdy'] \
        + b['C'][1:-1,1:-1,1:-1,2,2]*(b['uz'][1:-1,1:-1,1:] - b['uz'][1:-1,1:-1,:-1]) \
        / b['sdz']

def update_T4(b):
    b['T4'][1:-1,:,:] = b['C'][1:-1,1:,1:,3,3]*( \
        (b['uy'][1:-1,:,1:] - b['uy'][1:-1,:,:-1]) \
        / b['fdz'] \
        + (b['uz'][1:-1,1:,:] - b['uz'][1:-1,:-1,:]) \
        / b['fdy']
    )

def update_T5(b):
    b['T5'][:,1:-1,:] = b['C'][1:,1:-1,1:,4,4]*( \
        (b['ux'][:,1:-1,1:] - b['ux'][:,1:-1,:-1]) \
        / b['fdz'] \
        + (b['uz'][1:,1:-1,:] - b['uz'][:-1,1:-1,:])
        / b['fdx']
    )

def update_T6(b):
    b['T6'][:,:,1:-1] = b['C'][1:,1:,1:-1,5,5]*( \
        (b['ux'][:,1:,1:-1] - b['ux'][:,:-1,1:-1]) \
        / b['fdy'] \
        + (b['uy'][1:,:,1:-1] - b['uy'][:-1,:,1:-1]) \
        / b['fdx']
    )

def update_T1_tfbc(b):
    b['T1'][1:-1,1:-1,0] = \
        b['C'][1:-1,1:-1,0,0,0]*(b['ux'][1:,1:-1,0] - b['ux'][:-1,1:-1,0]) / b['sdx'][0,:,:] \
        + b['C'][1:-1,1:-1,0,0,1]*(b['uy'][1:-1,1:,0] - b['uy'][1:-1,:-1,0]) / b['sdy'][:,0,:] \
        + b['C'][1:-1,1:-1,0,0,2]*(b['uz'][1:-1,1:-1,0] - 0) / b['sdz'][:,:,0]

def update_T2_tfbc(b):
    b['T2'][1:-1,1:-1,0] = \
        b['C'][1:-1,1:-1,0,1,0]*(b['ux'][1:,1:-1,0] - b['ux'][:-1,1:-1,0]) / b['sdx'][0,:,:] \
        + b['C'][1:-1,1:-1,0,1,1]*(b['uy'][1:-1,1:,0] - b['uy'][1:-1,:-1,0]) / b['sdy'][:,0,:] \
        + b['C'][1:-1,1:-1,0,1,2]*(b['uz'][1:-1,1:-1,0] - 0) / b['sdz'][:,:,0]

def update_T4_tfbc(b):
    b['T4'][1:-1,:,0] = \
        b['C'][1:-1,1:,0,3,3] \
        * ((b['uy'][1:-1,:,1] - b['uy'][1:-1,:,0]) / b['fdy'][:,0,:] \
        + (b['uz'][1:-1,1:,0] - b['uz'][1:-1,:-1,0]) / b['fdz'][:,:,0])

def update_T5_tfbc(b):
    b['T5'][:,1:-1,0] = \
        b['C'][1:,1:-1,0,4,4] \
        * ((b['ux'][:,1:-1,1] - b['ux'][:,1:-1,0]) / b['fdx'][0,:,:] \
        + (b['uz'][1:,1:-1,0] - b['uz'][:-1,1:-1,0]) / b['fdz'][:,:,0])

def update_T6_tfbc(b):
    b['T6'][:,:,0] = \
        b['C'][1:,1:,0,5,5] \
        * ((b['ux'][:,1:,0] - b['ux'][:,:-1,0]) / b['fdx'][0,:,:] \
        + (b['uy'][1:,:,0] - b['uy'][:-1,:,0]) / b['fdz'][:,:,0])
