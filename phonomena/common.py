
cfg = None
mesh = None
material = None

def import_settings(path):
    global cfg
    import configparser
    cfg = configparser.ConfigParser()
    cfg.read(path)

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

def save_settings(path):
    pass
