import numpy as np
import h5py
from logging import getLogger

logger = getLogger(__name__)


def nonlinspace(spacing):
    '''
    Return array where spacing between each point is specified by the input var
    '''
    if len(spacing.shape) > 1:
        raise TypeError('Only supports 1D arrays')
    X = np.zeros((spacing.size))
    for i in range(1,len(spacing)):
        X[i] = X[i-1] + spacing[i]
    return X[:]

def trim_trailing_zeros(arr, threshold = 1):
    '''
    Remove zeros from array where 0 is any number under some threshold
    threshold: % of maximum value in arrays
    trim: front or back (fb is both)
    '''
    arr[arr < (threshold*np.max(arr)/100)] = 0
    if len(arr.shape) == 1:
        out = np.trim_zeros(arr, 'b')
        I = range(0, out.size)

    elif len(arr.shape) == 2:
        flattened = np.prod(arr, axis=0)
        temp = np.trim_zeros(flattened, 'b')
        I = range(0, temp.size)
        out = arr[:,I]
    else:
        raise TypeError("Only accepts 1D arrays")
    return out, I

def spectrum(file, u_id, z_index, y_index, x_index=None):
    '''
    Perform one or two dimensional spectrum analysis on HDF dataset
    x_index optional, enforcing 1D or 2D fft.

    https://stackoverflow.com/questions/3694918/how-to-extract-frequency-associated-with-fft-values-in-python
    '''
    hdf = None
    if type(file) == str:
        hdf = h5py.File(file,'r')
    elif type(file) == h5py.File:
        hdf = file
    else:
        raise TypeError
    try:
        u = hdf.get(u_id)
        assert u != None
        if u_id == 'ux':
            x = nonlinspace(hdf.attrs["fdx"][:,0,0])
        else:
            x = np.array(hdf.attrs["x"])
        dt = hdf.attrs["dt"]
        T = dt*u.shape[3]

        N = u.shape[3]
        Nf = N // 2
        f = np.fft.fftfreq(N, d=dt)[:Nf]
        window_fn = np.hanning(N)

        if x_index == None:
            # 2 dimensional FFT (x and t axes)
            dft = np.abs(np.fft.fft2(u[:,y_index,z_index,:]*window_fn))
            dft = dft[:,:Nf]

        else:
            # FOR DEBUG
            '''if __name__ =='__main__':
                t = np.linspace(0, dt*u.shape[3], u.shape[3])
                fig, ax = plt.subplots()
                ax.plot(t, u[x_index, y_index, z_index, :])
                plt.show()'''

            # 1 dimensional FFT (t axis only)
            dft = np.abs(np.fft.fft(u[x_index,y_index,z_index,:]*window_fn))
            dft = dft[:Nf]

    except Exception as e:
        raise e
    finally:
        if type(file) == str:
            hdf.close()

    return x, f, dft

if __name__ == '__main__':
    import matplotlib
    import matplotlib.pyplot as plt
    import sys
    np.set_printoptions(threshold=sys.maxsize)

    file = r'C:\Users\mattd\Documents\GitHub\phonomena\phonomena\simulation\test.hdf'

    x, f, dft = spectrum(file, 'ux', y_index=20, z_index=4, x_index=None)
    dft, I = trim_trailing_zeros(dft)
    f = f[I]
    #print(f[np.argmax(dft)])
    fig, ax = plt.subplots()
    #cf = ax.plot(f, dft)
    #plt.show()
    #quit()
    #print(x.shape, f.shape, dft.shape)
    X, F = np.meshgrid(x, f)
    cf = ax.contourf(F, X, dft.transpose(), 100)
    fig.colorbar(cf)
    plt.show()
