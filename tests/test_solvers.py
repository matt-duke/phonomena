from pathlib import Path
import sys
from time import time

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

import unittest
import phonomena
from phonomena import common
common.set_tmpdir()
#from phonomena.simulation import grid
#from phonomena.simulation import material

class TestSolvers(unittest.TestCase):

    def test_default(self):
        t1 = time()
        s = common.importSolver("simulation.solvers.solver_default")
        s.test()
        print(time()-t1)

    def test_numba(self):
        t1 = time()
        s = common.importSolver("simulation.solvers.solver_numba")
        s.test()
        print(time()-t1)


if __name__ == '__main__':
    unittest.main()
