#!/usr/bin/python3.7

import os
import time
from pathlib import Path
import PyInstaller.__main__

FAST = False

build_dir = Path('build')
work_dir = build_dir.joinpath('work')
dist_dir = build_dir.joinpath('build')
package_name = "phonomena"
data_dir = Path('data')
solver_dir = Path(package_name).joinpath("simulation", "solvers")
entrypoint = Path(package_name).joinpath('__main__.py')
info_file = Path(package_name).joinpath('info.py')

hidden_imports = ['simulation.base_solver', 'dill', 'numba', 'xmlrpc.client', 'xmlrpc.server', 'requests', 'pkg_resources.py2_warn']
hidden_imports = ('--hidden-import='+s for s in hidden_imports)

if os.name == 'nt':
    add_data = '--add-data={};{}'
elif os.name == 'posix':
    add_data = '--add-data={}:{}'

version = '0.9'
build_num = time.strftime('%j%y.%H%M%S')
print("Building...")
print('v.{}, b.{}'.format(version, build_num))

if not FAST:
    with open(info_file, 'w') as f:
        f.write('build = {}'.format(build_num))
        f.write('\n')
        f.write('version = {}'.format(version))
else:
    print('WARNING: building in fast mode, version file not updated.')

PyInstaller.__main__.run([
    '--name={}'.format(package_name),
    '--workpath={}'.format(work_dir),
    '--distpath={}'.format(dist_dir),
    '--specpath={}'.format(build_dir),
    '--onedir',
    '--console',
    *hidden_imports,
    '--paths={}'.format(package_name),
    add_data.format(data_dir.resolve(), data_dir),
    add_data.format(solver_dir.resolve(), 'solvers'),
    '--log-level=INFO',
    '--noconfirm', #remove output directory without confirmation
    str(entrypoint)
])
