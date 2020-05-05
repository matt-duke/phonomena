#!/usr/bin/python3.7

import os
import time
from pathlib import Path
import PyInstaller.__main__
import subprocess as sp
import sys

FAST = False
CONSOLE = False

build_dir = Path('build')
work_dir = build_dir.joinpath('work')
dist_dir = build_dir.joinpath('release')
package_name = "phonomena"
data_dir = Path('data')
solver_dir = Path(package_name).joinpath("simulation", "solvers")
entrypoint = Path(package_name).joinpath('__main__.py')
info_file = Path(package_name).joinpath('info.py')

hidden_imports = ['simulation.base_solver', 'dill', 'numba', 'xmlrpc.client', 'xmlrpc.server', 'requests', 'pkg_resources.py2_warn']
hidden_imports = ('--hidden-import='+s for s in hidden_imports)

excludes = ['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter']
excludes = ('--exclude-module='+s for s in excludes)

console_mode = '--console' if CONSOLE else '--windowed'

if os.name == 'nt':
    add_data = '--add-data={};{}'
elif os.name == 'posix':
    add_data = '--add-data={}:{}'

version = '2.0'
build_num = time.strftime('%j%y.%H%M')
print("Building...")
print('v.{}, b.{}'.format(version, build_num))

if not FAST:
    with open(info_file, 'w') as f:
        f.write('build = {}'.format(build_num))
        f.write('\n')
        f.write('version = {}'.format(version))
        f.write('\n')
        f.write('py_ver = "{}"'.format(sys.version).replace('\n',''))
        #f.write('py_ver = \"{}\"'.format(sp.check_output([sys.executable, "--version"]).strip().decode("utf-8")))
        #f.write('\n')
else:
    print('WARNING: building in fast mode, version file not updated.')

PyInstaller.__main__.run([
    '--name={}'.format(package_name),
    '--workpath={}'.format(work_dir),
    '--distpath={}'.format(dist_dir),
    '--specpath={}'.format(build_dir),
    '--onedir',
    *excludes,
    console_mode,
    *hidden_imports,
    '--paths={}'.format(package_name),
    add_data.format(data_dir.resolve(), data_dir),
    add_data.format(solver_dir.resolve(), 'solvers'),
    '--log-level=INFO',
    '--noconfirm', #remove output directory without confirmation
    str(entrypoint)
])
