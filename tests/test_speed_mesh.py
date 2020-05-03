from time import time
import cProfile
from pathlib import Path
import matplotlib as mp
import matplotlib.pyplot as plt

import test_setup

from phonomena import common
from phonomena.simulation import material, grid
from phonomena.simulation import base_solver
from phonomena.simulation import analysis


common.configureLogger()

solvers = [
    "solver_default",
    #"solver_numba",
    #"solver_threading"
]

files = ['fine.json', 'coarse.json', 'nonuniform.json']

steps = 500
repeat_test = 1

if __name__ == '__main__':
    for s in solvers:
        fpath = Path(__file__).resolve().parent.joinpath('data',file)
        solver = common.importSolver(s)
        common.loadSettings(fpath)
        for file in files:
            solver.init(common.grid, common.material, steps)
            t1 = time()
            #cProfile.run("solver.run()")
            solver.run()
            t2 =  time()-t1
            print("Total runtime (file: {}): {}".format(file, t2))

            print
            quit()

            x, freq, fft = analysis.spectrum(solver.file, 'uz', z_index=1, y_index=25, x_index=45)
            fig, ax = plt.subplots()
            cf = ax.plot(freq, fft)
            plt.show()
