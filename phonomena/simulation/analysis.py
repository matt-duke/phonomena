import numpy as np
import h5py

def spectrum(file, y_index=1, z_index=1):
    with h5py.File(file,'r') as hdf:
        u = np.array(hdf.get('uz'))
        grid_x = hdf.attrs["grid_x"]
        dt = hdf.attrs["dt"]
    fft = np.fft.rfft2(u[:,y_index,z_index,:])
    freq = np.fft.fftfreq(fft.shape[1], d=1/dt)
    freq = np.fft.fftshift(freq)

    return grid_x, freq, fft

if __name__ == '__main__':
    import matplotlib
    import matplotlib.pyplot as plt
    import sys
    np.set_printoptions(threshold=sys.maxsize)

    file = r'C:\Users\mattd\Documents\GitHub\phonomena\phonomena\simulation\default.hdf'

    x, f, fft = spectrum(file)
    #print(x.shape, f.shape, fft.shape)
    FFT = np.real(fft)
    F, X = np.meshgrid(f, x)
    fig, ax = plt.subplots()
    cf = ax.contourf(X, F, FFT, 100)
    fig.colorbar(cf)
    plt.show()
