import numpy as np
from transforms import make_angrad_func


def circle(t, r, a0=0):
    t_ = t + a0
    x = r * np.cos(t_)
    y = r * np.sin(t_)
    return np.array([x, y])


def involute(t, r, a0=0):
    """
    Involute of circle as a parametric equations: x(t), y(t). See https://en.wikipedia.org/wiki/Involute.

    Args:
        t: Polar angle of the tangent point.
        r: Circle radius.
        a0: Rotation angle.

    Returns:
        Coordinates of the point (x, y).
    """
    t_ = t + a0
    x = r * (np.cos(t_) + t * np.sin(t_))
    y = r * (np.sin(t_) - t * np.cos(t_))
    return np.array([x, y])


def epitrochoid(t, R, r, d, a0=0):
    """
    Epitrochoid as a parametric equations: x(t), y(t). See https://en.wikipedia.org/wiki/Epitrochoid.

    Args:
        t: Polar angle of the rolling circle center.
        R: Fixed circle radius.
        r: Rolling circle radius.
        d: Distance between the point and rolling circle center.
        a0: Rotation angle.

    Returns:
        Coordinates of the point (x, y).
    """
    t_ = t + a0
    x = (R + r) * np.cos(t_) - d * np.cos(R * t / r + t_)
    y = (R + r) * np.sin(t_) - d * np.sin(R * t / r + t_)
    return np.array([x, y])


def epitrochoid_flat(t, R, l, a0=0):
    """
    Epitrochoid as a parametric equations: x(t), y(t). Edge case when r = inf, i. e. line is rolling around the fixed
    circle. The point is fixed against the line.

    Args:
        t: Polar angle of the tangent point.
        R: Fixed circle radius.
        l: Distance between the point and line.
        a0: Rotation angle.

    Returns:
        Coordinates of the point (x, y).
    """
    t_ = t + a0
    x = (R - l) * np.cos(t_) + t * R * np.sin(t_)
    y = (R - l) * np.sin(t_) - t * R * np.cos(t_)
    return np.array([x, y])


involute_angrad = make_angrad_func(involute)
epitrochoid_angrad = make_angrad_func(epitrochoid)
epitrochoid_flat_angrad = make_angrad_func(epitrochoid_flat)
