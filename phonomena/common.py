import os, sys
import json
from pathlib import Path
import shutil
import logging
import multiprocessing as mp

logger = logging.getLogger(__name__)

try:
    import simulation
except:
    from . import simulation

class Info:
    version = 'none'
    build = 'none'

# Assign defaults to variables
info = Info
cfg = None
grid = None
material = None
solver_dict = {}
solver = None

# Defines whether package has been bundled using PyInstaller
DEBUG = hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS')

if not DEBUG:
    SOLVER_PKG = "simulation.solvers"
    SOLVER_DIR = Path(__file__).parent.joinpath(SOLVER_PKG.replace('.','/'))
    DATA_DIR = Path(__file__).parents[1].joinpath("data")
else:
    SOLVER_PKG = "solvers"
    SOLVER_DIR = Path(__file__).parent.joinpath(SOLVER_PKG.replace('.','/'))
    DATA_DIR = Path(__file__).parent.joinpath("data")
SETTINGS_FILE = DATA_DIR.joinpath("default.json")

FORMAT_STR = '[%(msecs)04d]:%(levelname)s:[%(name)s:%(lineno)d]:%(message)s'
LOG_LEVEL = logging.INFO
if __debug__:
    LOG_LEVEL = logging.DEBUG
LOG_FILE = 'debug.log'

def configureLogger():
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    logFormatter = logging.Formatter(FORMAT_STR)

    fileHandler = logging.FileHandler(LOG_FILE, mode='w')
    fileHandler.setLevel(LOG_LEVEL)
    fileHandler.setFormatter(logFormatter)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(LOG_LEVEL)

    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)

    modules = ['matplotlib', 'numba']
    for m in modules:
        l = logging.getLogger(m)
        l.setLevel(logging.WARNING)

def setTempdir():
    temp = Path.cwd().joinpath('tmp')
    if temp.is_dir():
        try:
            print("clearing")
            sys.stdout.flush()
            shutil.rmtree(temp)
            temp.mkdir()
        except Exception as e:
            logger.warning("Unable to clear tmp folder: {}".format(e))
    else:
        temp.mkdir()
    os.environ["TMPDIR"] = str(temp)

def configMultiprocessing():
    mp.freeze_support()
    mp.set_start_method('spawn')

# Returns solver object
def importSolver(module):
    mod = __import__('{}.{}'.format(SOLVER_PKG, module), fromlist=['Solver'])
    solver = getattr(mod, 'Solver')()
    return solver

def findSolvers():
    global solver_dict, solver
    solver_dict = {}

    dir = os.listdir(SOLVER_DIR)
    for f in dir:
        if '.py' not in f:
            continue
        f = f.replace('.py','')
        try:
            s = importSolver(f)
            solver_dict[s.name] = s
        except Exception as e:
            logger.error("Error importing solver {}: {}".format(f, e))

    logger.info("Found solvers: {}".format(list(solver_dict.keys())))
    #solver = list(solver_dict.keys())[0]
    solver = next(iter(solver_dict.values()))

def loadSettings(path=SETTINGS_FILE):
    global cfg, grid, material, solver, solver_dict
    cfg = json.load(open(path))

    # Setup grid from configuration file
    grid = simulation.grid.Grid()
    grid.init(
        size_x = cfg['grid']['size_x'],
        size_y = cfg['grid']['size_y'],
        size_z = cfg['grid']['size_z']
    )
    grid.min_d = cfg['grid']['min_d']
    grid.max_dx = cfg['grid']['max_dx']
    grid.max_dy = cfg['grid']['max_dy']
    grid.max_dz = cfg['grid']['max_dz']
    grid.slope = cfg['grid']['slope']

    for t in cfg["inclusions"]:
        grid.addInclusion(x=t['x'], y=t['y'], z=t['z'], r=t['r'])

    grid.buildMesh()
    grid.update()

    # Setup material
    material = simulation.material.Material()
    material.init(
        grid = grid,
        properties = cfg['material']['properties']
    )

    material.c_max = cfg['simulation']['courant']

    material.setPrimary(cfg['material']['primary'])
    material.setSecondary(cfg['material']['secondary'])
    material.update()

    s = cfg['simulation']['solver']
    if s in solver_dict.keys():
        solver = solver_dict[s]
        sim_cfg = cfg['simulation']['cfg']
        solver.cfg = {**solver.cfg, **sim_cfg}
    else:
        logger.error("Solver not found: {}".format(s))

    return cfg, grid, material

def saveSettings(path):
    global cfg, grid, material, solver
    cfg['grid'] = {
        "slope": grid.slope,
        "max_dx": grid.max_dx,
        "max_dy": grid.max_dy,
        "max_dz": grid.max_dz,
        "min_d": grid.min_d,
        "size_x": grid.size_x,
        "size_y": grid.size_y,
        "size_z": grid.size_z,
    }

    cfg['inclusions'] = [ {'x': float(row[0]), 'y':float(row[1]), 'z': float(row[2]), 'r':float(row[3])} for row in grid.targets ]

    cfg['simulation']['courant'] = material.c_max
    cfg['material']['primary'] = material.primary_key
    cfg['material']['secondary'] = material.secondary_key

    cfg['simulation']['solver'] = solver.name
    cfg['simulation']['cfg'] = solver.cfg

    with open(path, 'w') as file:
        json.dump(cfg, file)

def startupTasks():
    configureLogger()
    configMultiprocessing()
    setTempdir()

    global info

    try:
        import info
    except:
        logger.warning("Error loading info file.")


if __name__ == '__main__':
    importSettings()
    init()
    updateCfg()
