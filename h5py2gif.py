import h5py
import imageio
import numpy as np
import matplotlib.pyplot as plt
import os

def clear():
    print("Clearing img cache...")
    for f in os.listdir("img"):
        os.remove("img/{}".format(f))
    print("Done.")

def generate(rng_modifier=1, const_scale=False, skip=1):
    num_img = 0

    hdf = h5py.File('test.hdf5', 'r')
    print(list(hdf.keys()))
    u = hdf.get('uz')
    x = hdf.attrs['x']
    y = hdf.attrs['y']

    size_x, size_y = (u.shape[0], u.shape[1])
    X, Y = np.meshgrid(x[:size_x], y[:size_y])
    iz = 0

    levels = None
    if const_scale:
        umin = rng_modifier*np.amin(u[:,:,iz,:])
        umax = rng_modifier*np.amax(u[:,:,iz,:])
        levels = np.linspace(umin, umax, 100)
        print(levels)
    print("Generating png...")
    for it in range(0, u.shape[3]):
        num_img += 1
        if (num_img % skip != 0):
            continue
        filename = "frame{:05d}.png".format(num_img)
        filepath = "img/{}".format(filename)
        if (filename in os.listdir("img/")):
            print("skipping {}".format(filename))    
            continue
        print("generating {}".format(filename))
        plt.clf()
        Z = u[:,:,iz,it].transpose()
        if const_scale:
            plt.contourf(X, Y, Z, levels, extend='both')
        else:
            plt.contourf(X, Y, Z, 100)
        plt.savefig(filepath)
    print("Done.")

def make_gif(fps):
    print("Writing...")
    gif = 'output.gif'
    if os.path.exists(gif):
        os.remove(gif)
    with imageio.get_writer(gif, mode='I', fps=fps) as writer:
        for name in os.listdir("img"):
            filename = "img/{}".format(name)
            image = imageio.imread(filename)
            print("writing {} to gif".format(filename))
            writer.append_data(image)
    print("Done.")

#images = []
#for fn in os.listdir("img"):
#    images.append(imageio.imread("img/{}".format(fn)))
#imageio.mimsave('output.gif', images, fps=25)

if __name__ == '__main__':
    clear()
    generate(0.05, True, skip=3)
    make_gif(100)