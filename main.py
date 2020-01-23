import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from config import Config
from grid import Grid
from material import Material
from solver import Solver

def main():

    conf = Config()
    p1 = conf.p_GaAs # density
    c1 = conf.c_GaAs # elastic stiffness
    p2 = conf.p_Al
    c2 = conf.c_Al

    g = Grid(conf.dim)
    m = Material(conf.dim, g, p1, c1, p2, c2)
    m.set_main_material(g, p1, c1)
    #m.set_inclusion_material(g, p2, c2)
    s = Solver(g, m)
    print(g.dt)


    plt.figure()
    plt.pcolor(m.P[:,:,0]);
    plt.xlabel('x')
    plt.ylabel('y')
    plt.axis('scaled')
    plt.savefig('img/lattice.png', transparent=True)

    fig = plt.figure()
    ims = []

    for tt in range(conf.num_steps):
        g.uz[0, :, 0] = s.update_ricker(tt)
        s.update_T()
        s.update_T_BC()
        s.update_u()
        s.update_u_BC()
        s.time_step()

        #mesh = g.uz[:, int(g.size_y/2), :]
        #im = plt.pcolor(np.flipud(mesh.T)/np.max(mesh))

        mesh = g.uz[:, :, 0]
        im = plt.imshow(mesh, animated=True)
        ims.append([im])
        #im.axis('scaled')
        #print(tt)
    print("saving")
    ani = animation.ArtistAnimation(fig, ims, interval=1, blit=True,
                                repeat_delay=1000)
    ani.save('test.gif', writer="pillow")
    print("done")

    if plot:
        """pl.figure()
        mesh = g.uz[:, :, 0]
        pl.pcolor(mesh/np.max(mesh))
        pl.colorbar()
        pl.xticks([], [])
        pl.yticks([], [])
        pl.xlabel('x')
        pl.ylabel('y')
        pl.axis('scaled')
        pl.savefig('img/sim-top.png', bbox_inches='tight', transparent=True)"""

def profile(path=None):
    if path == None:
        cProfile.run('main()')
    else:
        cProfile.run('main()', path)
        read(path)

def read(path):
    p = pstats.Stats(path)
    p.sort_stats('tottime')
    p.print_stats()

def profile():
    from solvers.solver_multiprocess import Solver
    profile("profiles/fall_report/desktop-multiprocess-1500")
    from solvers.solver_threading import Solver
    profile("profiles/fall_report/desktop-threading-1500")
    from solvers.solver_master import Solver
    profile("profiles/fall_report/desktop-master-1500")

if __name__ == '__main__':
    from solvers.solver_threading import Solver
    main(True)
