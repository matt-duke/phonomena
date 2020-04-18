if __name__ == '__main__':
    from time import time
    import cProfile
    import unittest
    import multiprocessing as mp
    mp.freeze_support()

    import test_setup

    from phonomena import common
    from phonomena.simulation import material, grid
    from phonomena.simulation import base_solver

    common.configureLogger()
    common. setTempdir()

    g = grid.Grid()
    g.init(
        size_x = 50,
        size_y = 50,
        size_z = 10
    )

    m = material.Material()
    m.init(
        grid = g,
        properties = base_solver.TestDefaults.properties
    )
    m.setPrimary("GaAs")
    m.setSecondary("GaAs")

    g.buildMesh()
    g.update()
    m.update()

    solvers = [
        "solver_default",
        #"solver_numba",
        #"solver_threading"
    ]

    steps = [1000]

    repeat_test = 1

    for s in solvers:
        for tt in steps:
            t_time = 0
            for n in range(repeat_test):
                solver = common.importSolver(s)
                solver.cfg['write_mode'] = 'process'
                solver.init(g, m, tt)
                t1 = time()
                #cProfile.run("solver.run()")
                solver.run()
                t2 =  time()-t1
                t_time += t2
                print("run {}: {} completed {} steps in {}s".format(n, s, tt, t2))
            print("{} runs in {}s ({}s avg)".format(repeat_test, t_time, t_time/repeat_test))
