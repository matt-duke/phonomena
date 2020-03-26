import threading
from queue import Queue
from multiprocessing import cpu_count

from simulation import base_solver

import logging
logger = logging.getLogger(__name__)

cfg = {
    "use_threading": True,
}

class Solver(base_solver.BaseSolver):

    def __init__(self):
        super().__init__(logger)
        self.name = "threading"
        self.description = "<p></p>"
        self.cfg = cfg

    def init(self, grid, material, steps):
        super().init(grid, material, steps)

        self.threads = []
        self.worker_queue = Queue()
        num_threads = cpu_count()
        for i in range(num_threads):
            t = threading.Thread(target=Solver.worker, args=(i, self.worker_queue))
            t.daemon = True
            t.start()
            self.threads.append(t)

    @staticmethod
    def worker(i, q):
        while True:
            fn, args = q.get()
            fn(*args)
            q.task_done()
            #print("{}: task done".format(i))


    def update_T(self):

        def T1(g, m):
            g.T1[1:-1,1:-1,1:-1] = \
              m.C[1:-1,1:-1,1:-1,0,0]*(g.ux[1:,1:-1,1:-1] - g.ux[:-1,1:-1,1:-1]) \
            / g.sdx \
            + m.C[1:-1,1:-1,1:-1,0,1]*(g.uy[1:-1,1:,1:-1] - g.uy[1:-1,:-1,1:-1]) \
            / g.sdy \
            + m.C[1:-1,1:-1,1:-1,0,2]*(g.uz[1:-1,1:-1,1:] - g.uz[1:-1,1:-1,:-1]) \
            / g.sdz

        def T2(g, m):
            g.T2[1:-1,1:-1,1:-1] = \
              m.C[1:-1,1:-1,1:-1,1,0]*(g.ux[1:,1:-1,1:-1] - g.ux[:-1,1:-1,1:-1]) \
            / g.sdx \
            + m.C[1:-1,1:-1,1:-1,1,1]*(g.uy[1:-1,1:,1:-1] - g.uy[1:-1,:-1,1:-1]) \
            / g.sdy \
            + m.C[1:-1,1:-1,1:-1,1,2]*(g.uz[1:-1,1:-1,1:] - g.uz[1:-1,1:-1,:-1]) \
            / g.sdz

        def T3(g, m):
            g.T3[1:-1,1:-1,1:-1] = \
                m.C[1:-1,1:-1,1:-1,2,0]*(g.ux[1:,1:-1,1:-1] - g.ux[:-1,1:-1,1:-1]) \
                / g.sdx \
                + m.C[1:-1,1:-1,1:-1,2,1]*(g.uy[1:-1,1:,1:-1] - g.uy[1:-1,:-1,1:-1]) \
                / g.sdy \
                + m.C[1:-1,1:-1,1:-1,2,2]*(g.uz[1:-1,1:-1,1:] - g.uz[1:-1,1:-1,:-1]) \
                / g.sdz

        def T4(g, m):
            g.T4[1:-1,:,:] = m.C[1:-1,1:,1:,3,3]*( \
                (g.uy[1:-1,:,1:] - g.uy[1:-1,:,:-1]) \
                / g.fdz \
                + (g.uz[1:-1,1:,:] - g.uz[1:-1,:-1,:]) \
                / g.fdy
            )

        def T5(g, m):
            g.T5[:,1:-1,:] = m.C[1:,1:-1,1:,4,4]*( \
                (g.ux[:,1:-1,1:] - g.ux[:,1:-1,:-1]) \
                / g.fdz \
                + (g.uz[1:,1:-1,:] - g.uz[:-1,1:-1,:])
                / g.fdx
            )

        def T6(g, m):
            g.T6[:,:,1:-1] = m.C[1:,1:,1:-1,5,5]*( \
                (g.ux[:,1:,1:-1] - g.ux[:,:-1,1:-1]) \
                / g.fdy \
                + (g.uy[1:,:,1:-1] - g.uy[:-1,:,1:-1]) \
                / g.fdx
            )

        if not self.cfg['use_threading']:
            T1(self.g, self.m)
            T2(self.g, self.m)
            T3(self.g, self.m)
            T4(self.g, self.m)
            T5(self.g, self.m)
            T6(self.g, self.m)
        else:
            self.worker_queue.put((T1, (self.g, self.m)))
            self.worker_queue.put((T2, (self.g, self.m)))
            self.worker_queue.put((T3, (self.g, self.m)))
            self.worker_queue.put((T4, (self.g, self.m)))
            self.worker_queue.put((T5, (self.g, self.m)))
            self.worker_queue.put((T6, (self.g, self.m)))
            self.worker_queue.join()
            assert self.worker_queue.empty()


    def apply_T_tfbc(self):

        def T1(g, m):
            g.T1[1:-1,1:-1,0] = \
                m.C[1:-1,1:-1,0,0,0]*(g.ux[1:,1:-1,0] - g.ux[:-1,1:-1,0]) / g.sdx[0,:,:] \
                + m.C[1:-1,1:-1,0,0,1]*(g.uy[1:-1,1:,0] - g.uy[1:-1,:-1,0]) / g.sdy[:,0,:] \
                + m.C[1:-1,1:-1,0,0,2]*(g.uz[1:-1,1:-1,0] - 0) / g.sdz[:,:,0]

        def T2(g, m):
            g.T2[1:-1,1:-1,0] = \
                m.C[1:-1,1:-1,0,1,0]*(g.ux[1:,1:-1,0] - g.ux[:-1,1:-1,0]) / g.sdx[0,:,:] \
                + m.C[1:-1,1:-1,0,1,1]*(g.uy[1:-1,1:,0] - g.uy[1:-1,:-1,0]) / g.sdy[:,0,:] \
                + m.C[1:-1,1:-1,0,1,2]*(g.uz[1:-1,1:-1,0] - 0) / g.sdz[:,:,0]

        def T4(g, m):
            g.T4[1:-1,:,0] = \
                m.C[1:-1,1:,0,3,3] \
                * ((g.uy[1:-1,:,1] - g.uy[1:-1,:,0]) / g.fdy[:,0,:] \
                + (g.uz[1:-1,1:,0] - g.uz[1:-1,:-1,0]) / g.fdz[:,:,0])

        def T5(g, m):
            g.T5[:,1:-1,0] = \
                m.C[1:,1:-1,0,4,4] \
                * ((g.ux[:,1:-1,1] - g.ux[:,1:-1,0]) / g.fdx[0,:,:] \
                + (g.uz[1:,1:-1,0] - g.uz[:-1,1:-1,0]) / g.fdz[:,:,0])

        def T6(g, m):
            g.T6[:,:,0] = \
                m.C[1:,1:,0,5,5] \
                * ((g.ux[:,1:,0] - g.ux[:,:-1,0]) / g.fdx[0,:,:] \
                + (g.uy[1:,:,0] - g.uy[:-1,:,0]) / g.fdz[:,:,0])

        if not self.cfg['use_threading']:
            T1(self.g, self.m)
            T2(self.g, self.m)
            self.g.T3[1:-1,1:-1,0] = 0
            T4(self.g, self.m)
            T5(self.g, self.m)
            T6(self.g, self.m)
        else:
            self.worker_queue.put((T1, (self.g, self.m)))
            self.worker_queue.put((T2, (self.g, self.m)))
            self.worker_queue.put((T4, (self.g, self.m)))
            self.worker_queue.put((T5, (self.g, self.m)))
            self.worker_queue.put((T6, (self.g, self.m)))
            self.g.T3[1:-1,1:-1,0] = 0
            self.worker_queue.join()
            assert self.worker_queue.empty()
