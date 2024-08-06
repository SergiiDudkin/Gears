import numpy as np
import numpy.typing as npt

from .transforms import make_angrad_func

ArrOrNum = npt.NDArray | float


def circle(t: ArrOrNum, r: float, a0: float = 0) -> npt.NDArray:
    t_ = t + a0
    x = r * np.cos(t_)
    y = r * np.sin(t_)
    return np.array([x, y])


def involute(t: ArrOrNum, r: float, a0: float = 0) -> npt.NDArray:
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


def epitrochoid(t: ArrOrNum, R: float, r: float, d: float, a0: float = 0) -> npt.NDArray:
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


def epitrochoid_flat(t: ArrOrNum, R: float, l: float, a0: float = 0) -> npt.NDArray:  # noqa: E741
    """
    Epitrochoid as a parametric equations: x(t), y(t). Edge case when r = inf, i.e. line is rolling around the fixed
    circle. The point is fixed at certain distance against the line.

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
