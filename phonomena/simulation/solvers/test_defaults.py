import numpy as np
from simulation import material, grid

properties = { "GaAs":
    {
        "p": 5307,
        "c": np.array([
            [11.88, 5.87, 5.38, 0, 0, 0],
            [5.87, 11.88, 5.38, 0, 0, 0],
            [5.87, 5.38, 11.88, 0, 0, 0],
            [0, 0, 0, 5.94, 0, 0],
            [0, 0, 0, 0, 5.94, 0],
            [0, 0, 0, 0, 0, 5.94]
        ])
    }
}


g = grid.Grid(
    size_x = 4,
    size_y = 5,
    size_z = 6
)

m = material.Material(
    grid = g,
    propeties = properties
)

g.min_d = 1
g.max_dx = 1
g.max_dy = 1
g.max_dz = 1
g.slope = 0
g.buildMesh()
m.setMaterials(
    m1 = "GaAs",
    m2 = "GaAs"
)
