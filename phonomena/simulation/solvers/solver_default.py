from simulation import base_solver

import logging
logger = logging.getLogger(__name__)

class Solver(base_solver.BaseSolver):

    def __init__(self):
        super().__init__(logger)

        self.name = "default"
        self.description = "<p></p>"
