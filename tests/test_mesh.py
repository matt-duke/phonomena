import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path

import test_setup

from phonomena import common
from phonomena.simulation import material, grid
from phonomena.simulation import base_solver

file = 'data/coarse.json'
fpath = Path(__file__).resolve().parent.joinpath(file)
common.loadSettings(fpath)

m = common.material
g = common.grid

fig, ax = plt.subplots()
#cf = ax.pcolormesh(g.x[1:-1], g.y[1:-1], m.P[1:-1, 1:-1, 0])
x = np.mean([g.x[:-1], g.x[1:]], axis=0)
#x = np.concatenate(((-0.5, 0,), x))
y = np.mean([g.y[:-1], g.y[1:]], axis=0)
#y = np.concatenate(((-0.5, 0,), y))

#x = np.concatenate((g.x,(10.5,)))
#y = np.concatenate((g.y,(10.5,)))

X, Y = np.meshgrid(x,y)

#np.savetxt('test.csv', m.P[:,:,0], delimiter=',')
cf = ax.pcolormesh(X, Y, m.P[1:-1,1:-1,0].transpose())

ax.set_xticks(g.x)
ax.set_yticks(g.y)
#ax.set_xticks(range(50))
#ax.set_yticks(range(50))
plt.grid()
#cf = ax.pcolormesh(m.P[:,:,0])
plt.axis('equal')
plt.show()
quit()

fig, ax = plt.subplots()
cf = ax.pcolormesh(m.P[:,:,0])
plt.axis('equal')
plt.show()

quit()
steps = 100
s = 'solver_default'
solver = common.importSolver(s)
solver.init(grid = g, material = m, steps = steps)
solver.run()
