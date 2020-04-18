import bohrium
import os

from simulation import base_solver

import logging
logger = logging.getLogger(__name__)


cfg = {'bh_stack': 'opencl'}

class Solver(base_solver.BaseSolver):

    def __init__(self):
        super().__init__(logger)

        self.name = "bohrium"
        self.description = "<p></p>"
        self.cfg = {**cfg, **self.cfg}

    def init(self, grid, material, steps):

        assert cfg['bh_stack'] in ['openmp', 'opencl', 'cuda']
        os.environ["BH_STACK"] = self.cfg['bh_stack']

        grid.T1 = bohrium.array(grid.T1)
        grid.T2 = bohrium.array(grid.T2)
        grid.T3 = bohrium.array(grid.T3)
        grid.T4 = bohrium.array(grid.T4)
        grid.T5 = bohrium.array(grid.T5)
        grid.T6 = bohrium.array(grid.T6)

        grid.ux_new = bohrium.array(grid.ux_new)
        grid.uy_new = bohrium.array(grid.uy_new)
        grid.uz_new = bohrium.array(grid.uz_new)

        material.C = bohrium.array(material.C)
        material.P = bohrium.array(material.P)

        super().init(grid, material, steps)
