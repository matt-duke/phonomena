import os
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

packages = ['matplotlib', 'PyQt5', 'numpy', 'h5py', 'numba', 'requests', 'dill', 'PyInstaller']

if os.name == 'nt':
    packages.append('pypiwin32')
elif os.name == 'posix':
    packages.append('bohrium')

for package in packages:
     install(package)
