if __name__ == '__main__':
    from time import time
    import cProfile
    import csv

    import test_setup

    from phonomena import common
    from phonomena.simulation import material, grid
    from phonomena.simulation import base_solver

    common.startupTasks()

    g = grid.Grid()
    g.init(
        size_x = 60,
        size_y = 60,
        size_z = 20
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
        "solver_numba",
        "solver_threading",
        "solver_multiprocess"
    ]

    step_arr = list(range(1000, 5001, 1000))
    repeat_test = 3

    with open('tests/results/speed.csv', mode='w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, dialect='excel', delimiter=',')
        csvwriter.writerow(['solver', 'trial', 'steps', 'points', 'runtime', 'cfg'])
        for s in solvers:
            solver = common.importSolver(s)
            solver.cfg['write_mode'] = 'off'
            for steps in step_arr:
                t_time = 0
                for n in range(repeat_test):
                    points = g.x.size*g.y.size*g.z.size
                    solver.init(g, m, steps)
                    t1 = time()
                    #cProfile.run("solver.run()")
                    solver.run()
                    t2 =  time()-t1
                    t_time += t2
                    print("run {}: {} completed {} steps in {}s".format(n+1, s, steps, t2))
                    csvwriter.writerow([solver.name, n+1, steps, points, t2, str(solver.cfg)])
                print("{} runs in {}s ({}s avg)".format(repeat_test, t_time, t_time/repeat_test))
