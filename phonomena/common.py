import os

cfg = None
mesh = None
material = None

data_path = "data"
settings_path = os.path.join(data_path, "settings.cfg")


def import_settings(path=settings_path):
    global cfg
    import configparser

    assert os.path.exists(path)
    cfg = configparser.ConfigParser()
    cfg.read(settings_path)

# Add test requirements
def test_cfg():
    global cfg

def init():
    from simulation import grid, material
    global cfg, mesh, material
    assert cfg != None
    mesh = grid.Grid(
        cfg.getint('MESH', 'x'),
        cfg.getint('MESH', 'y'),
        cfg.getint('MESH', 'z')
    )

def save_settings(path=""):
    global cfg, mesh, material
    print(mesh.size_x)
    cfg.set('MESH', 'x', str(mesh.size_x))
    cfg.set('MESH', 'y', str(mesh.size_y))
    cfg.set('MESH', 'z', str(mesh.size_z))

    path = settings_path if path == "" else path
    with open(path, 'w') as configfile:
        cfg.write(configfile)
