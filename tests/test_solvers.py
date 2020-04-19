if __name__ == "__main__":

    from pathlib import Path
    import sys
    from time import time

    import test_setup

    import unittest
    import phonomena
    from phonomena import common
    common.setTempdir()
    #from phonomena.simulation import grid
    #from phonomena.simulation import material

    class TestSolvers(unittest.TestCase):

        def test_default(self):
            t1 = time()
            s = common.importSolver("solver_default")
            s.cfg['write_mode'] = 'off'
            s.test()
            print(time()-t1)

        def test_numba(self):
            t1 = time()
            s = common.importSolver("solver_numba")
            s.cfg['write_mode'] = 'off'
            s.test()
            print(time()-t1)


if __name__ == '__main__':
    unittest.main()
