import numpy as np


def circle(t, r, a0=0):
    t_ = t + a0
    x = r * np.cos(t_)
    y = r * np.sin(t_)
    return np.array([x, y])


def involute(t, r, a0=0):
    t_ = t + a0
    x = r * (np.cos(t_) + t * np.sin(t_))
    y = r * (np.sin(t_) - t * np.cos(t_))
    return np.array([x, y])


def epitrochoid(t, R, r, d, a0=0):
    t_ = t + a0
    x = (R + r) * np.cos(t_) - d * np.cos(R * t / r + t_)
    y = (R + r) * np.sin(t_) - d * np.sin(R * t / r + t_)
    return np.array([x, y])


def epitrochoid_flat(t, R, l, a0=0):
    t_ = t + a0
    x = (R - l) * np.cos(t_) + t * R * np.sin(t_)
    y = (R - l) * np.sin(t_) - t * R * np.cos(t_)
    return np.array([x, y])
