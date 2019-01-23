import numpy as np
from os.path import realpath, join, dirname


def get_module_corner_coords():
    dir_ = realpath(dirname(__file__))
    coords = np.load(join(dir_, "module_corner_coords.npy"))
    return coords


def get_module_corner_triangle_coords():
    dir_ = realpath(dirname(__file__))
    coords = np.load(join(dir_, "module_corner_tri_coords.npy"))
    return coords
