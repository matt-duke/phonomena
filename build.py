import os
import time
import PyInstaller.__main__

FAST = False

build_dir = 'build'
work_dir = os.path.join(build_dir, 'work')
dist_dir = os.path.join(build_dir, 'dist')
package_name = "phonomena"
data_dir = 'data'
solver_dir = os.path.join(package_name, "simulation", "solvers")
entrypoint = os.path.join(package_name, '__main__.py')
info_file = os.path.join(package_name, 'info.py')

hidden_imports = ['simulation.base_solver', 'dill', 'numba', 'xmlrpc', 'requests', 'pkg_resources.py2_warn']

hidden_imports = ('--hidden-import='+s for s in hidden_imports)

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
    '--add-data={};{}'.format(os.path.realpath(data_dir), data_dir),
    '--add-data={};{}'.format(os.path.realpath(solver_dir), 'solvers'),
    '--log-level=INFO',
    '--noconfirm', #remove output directory without confirmation
    entrypoint
])
