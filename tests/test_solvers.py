from pathlib import Path
import sys

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

import unittest
import phonomena
from phonomena import common
#from phonomena.simulation import grid
#from phonomena.simulation import material

class TestSolvers(unittest.TestCase):

    def test_default(self):
        common.solver = common.importSolver("simulation.solvers.solver_default")
        common.solver.test()

if __name__ == '__main__':
    unittest.main()
