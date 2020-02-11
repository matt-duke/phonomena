import os

cfg = None
mesh = None
material = None

data_path = "data"
settings_path = os.path.join(data_path, "default.json")


def import_settings(path=settings_path):
    global cfg
    import json

    assert os.path.exists(path)
    cfg = json.load(open(settings_path))

def saveSettings(path=""):
    updateCfg()
    path = settings_path if path == "" else path
    with open(settings_path, 'w') as file:
        json.dump(cfg, file)

def updateCfg():
    global cfg, mesh, material

    cfg = { "mesh":
             { "slope": mesh.slope,
               "max_dx": mesh.max_dx,
               "max_dy": mesh.max_dy,
               "min_d": mesh.min_d,
               "size_x": mesh.size_x,
               "size_y": mesh.size_y,
               "size_z": mesh.size_z,
             }
          }
    cfg['inclusions'] = [ {'x': row[0], 'y': row[1], 'r':row[2]} for row in mesh.targets ]

def init():
    from simulation import grid, material
    global cfg, mesh, material
    assert cfg != None
    mesh = grid.Grid(
        cfg['mesh']['size_x'],
        cfg['mesh']['size_y'],
        cfg['mesh']['size_z']
    )
    mesh.min_d = cfg['mesh']['min_d']
    mesh.max_dx = cfg['mesh']['max_dx']
    mesh.max_dy = cfg['mesh']['max_dy']
    mesh.slope = cfg['mesh']['slope']

    for t in cfg["inclusions"]:
        mesh.addInclusion(t['x'], t['y'], t['r'])

if __name__ == '__main__':
    import_settings()
    init()
    updateCfg()
