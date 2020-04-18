from simulation import base_solver

import logging
logger = logging.getLogger(__name__)

cfg = {}

class Solver(base_solver.BaseSolver):

    def __init__(self):
        '''
        Add features to constuctor, specifically a name and description for the GUI to display
        '''
        super().__init__(logger)

        self.name = "default"
        self.description = "<p></p>"
        # Combine global and default class cfg object - important to add settings
        self.cfg = {**cfg, **self.cfg}


    def init(self, grid, material, steps):
        '''
        Optionally overwrite default init function to add features
        For example the cfg object is made global here for out-of-scope functions that use it
        '''
        cfg = self.cfg
        super().init(grid, material, steps)

    def run(self, *args, **kwargs):
        '''
        Optionally overwrite default run function to add features
        Function inputs must mirror the default and forward all args amd kwargs
        '''
        super().run(*args, **kwargs)
