from pathlib import Path
import sys
from time import time
import cProfile

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

import unittest
import phonomena
from phonomena import common
from phonomena.simulation import material, grid
from phonomena.simulation import test_defaults

common.set_tmpdir()

g = grid.Grid(
    size_x = 100,
    size_y = 100,
    size_z = 50
)

m = material.Material(
    grid = g,
    properties = test_defaults.properties
)

g.min_d = 1
g.max_dx = 1
g.max_dy = 1
g.max_dz = 1
g.slope = 0
g.buildMesh()
m.setPrimary("GaAs")
m.setSecondary("GaAs")

solvers = [
    #"simulation.solvers.solver_default",
    #"simulation.solvers.solver_numba",
    "simulation.solvers.solver_threading"
]

steps = [10000]

repeat_test = 5


if __name__ == '__main__':
    g = test_defaults.g
    m = test_defaults.m
    for s in solvers:
        for tt in steps:
            t_time = 0
            for n in range(repeat_test):
                solver = common.importSolver(s)
                solver.init(g, m, tt)
                t1 = time()
                #cProfile.run("solver.run()")
                solver.run()
                t2 =  time()-t1
                t_time += t2
                print("run {}: {} completed {} steps in {}s".format(n, s, tt, t2))
            print("{} runs in {}s ({}s avg)".format(repeat_test, t_time, t_time/repeat_test))
