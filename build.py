import os
import PyInstaller.__main__


build_dir = 'build'
work_dir = os.path.join(build_dir, 'work')
dist_dir = os.path.join(build_dir, 'dist')
package_name = "phonomena"
data_dir = 'data'
entrypoint = os.path.join(package_name, '__main__.py')

PyInstaller.__main__.run([
    '--name={}'.format(package_name),
    '--workpath={}'.format(work_dir),
    '--distpath={}'.format(dist_dir),
    '--specpath={}'.format(build_dir),
    '--onedir',
    '--console',
    '--add-data={};{}'.format(os.path.realpath(data_dir), data_dir),
    '--log-level=INFO',
    '--noconfirm', #remove output directory without confirmation
    entrypoint
])
