import os, sys
import json

cfg = None
grid = None
material = None
solver_list = []
solver = None

data_path = "data"
settings_path = os.path.join(data_path, "default.json")
sys.path.insert(0, data_path)


# Returns solver object
def importSolver(module):
    mod = __import__(module, fromlist=['Solver'])
    solver = getattr(mod, 'Solver')()
    return solver

def findSolvers():
    global solver_list, solver
    solver_list = []

    default_solver = importSolver("simulation.solvers.solver_default")
    solver_list.append(default_solver)
    solver = default_solver

def importSettings(path=settings_path):
    global cfg

    assert os.path.exists(path)
    cfg = json.load(open(settings_path))

def updateCfg():
    global cfg, grid, material

    cfg = { "grid":
             { "slope": grid.slope,
               "max_dx": grid.max_dx,
               "max_dy": grid.max_dy,
               "max_dz": grid.max_dz,
               "min_d": grid.min_d,
               "size_x": grid.size_x,
               "size_y": grid.size_y,
               "size_z": grid.size_z,
             }
          }
    cfg['inclusions'] = [ {'x': row[0], 'y': row[1], 'z': row[2], 'r':row[3]} for row in grid.targets ]

def saveSettings(path):
    updateCfg()
    with open(path, 'w') as file:
        json.dump(cfg, file)

def init():
    import simulation.grid
    import simulation.material
    global cfg, grid, material

    if cfg != None:
        importSettings()
    assert cfg != None

    findSolvers()

    # Setup grid from configuration file
    grid = simulation.grid.Grid(
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
    # Setup material
    material = simulation.material.Material(
        grid = grid,
        propeties = cfg['material']['properties']
    )

    m1 = cfg['material']['primary']
    m2 = cfg['material']['secondary']
    material.setMaterials(m1, m2)

if __name__ == '__main__':
    importSettings()
    init()
    updateCfg()
