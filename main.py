import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as pl

from config import Config
from grid import Grid
from material import Material
from solver import Solver

def main():

    conf = Config()
    p1 = conf.p_GaAs
    c1 = conf.c_GaAs
    p2 = conf.p_Al
    c2 = conf.c_Al

    g = Grid(conf.dim)
    m = Material(conf.dim, g, p1, c1, p2, c2)
    m.set_main_material(g, p1, c1)
    m.set_inclusion_material(g, p2, c2)
    solv = Solver(g)
    print(g.dt)

    for tt in range(conf.num_steps):
        g.uz[0, :, 0] = solv.update_ricker(g, tt)
        solv.update_T(g, m)
        solv.update_T_BC(g, m)
        solv.update_u(g)
        solv.update_u_BC(g, m)
        solv.time_step(g)
        print(tt)

    pl.figure()
    mesh = g.uz[:, :, 0]
    pl.pcolor(mesh.T/np.max(mesh))
    pl.colorbar()
    pl.xticks([], [])
    pl.yticks([], [])
    pl.xlabel('x')
    pl.ylabel('y')
    pl.savefig('img/sim-top.png', bbox_inches='tight')

    pl.figure()
    mesh = g.uz[:, int(g.size_y/2), :]
    pl.pcolor(np.flipud(mesh.T)/np.max(mesh))
    pl.colorbar()
    pl.xticks([], [])
    pl.yticks([], [])
    pl.xlabel('x')
    pl.ylabel('z')
    pl.savefig('img/sim-side.png', bbox_inches='tight')

if __name__ == '__main__':
    main()
