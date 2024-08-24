from typing import Callable
from typing import cast
from typing import TypeVar

import numpy as np
import numpy.typing as npt
from scipy.interpolate import interp1d  # type: ignore[import-untyped]

from .helpers import stack_curves

ArrOrNumG = TypeVar('ArrOrNumG', np.ndarray, float)


def cartesian_to_polar(x: ArrOrNumG, y: ArrOrNumG) -> tuple[ArrOrNumG, ArrOrNumG]:
    ang = np.remainder(np.arctan2(y, x), np.pi * 2)
    rad = np.linalg.norm([x, y])  # type: ignore[attr-defined]
    return ang, rad


def polar_to_cartesian(ang: ArrOrNumG, rad: ArrOrNumG) -> tuple[ArrOrNumG, ArrOrNumG]:
    x = rad * np.cos(ang)
    y = rad * np.sin(ang)
    return x, y


def mirror(poi: npt.NDArray, seg_st: npt.NDArray, seg_en: npt.NDArray) -> npt.NDArray:
    """
    Reflect the point relative to the mirror line. It is XY-invariant.

    Args:
        poi: Point to be reflected.
        seg_st: First point of the mirror line
        seg_en: Second point of the mirror line

    Returns:
        Reflected point.
    """
    seg = seg_en - seg_st  # The segment vector
    proj_poi = seg_st + seg * np.vdot(seg, poi - seg_st) / np.vdot(seg, seg)  # Point of projection
    mirror_poi = proj_poi * 2 - poi  # Reflected point
    return mirror_poi


def rotate(x: ArrOrNumG, y: ArrOrNumG, angle: float) -> npt.NDArray:
    """
    Rotate points around the origin.

    Args:
        x: Radius-vector, x-value.
        y: Radius-vector, y-value.
        angle: Rotation angle, ACW, in radians.

    Returns:
        Rotated radius-vector.
    """
    return np.array([x * np.cos(angle) - y * np.sin(angle), x * np.sin(angle) + y * np.cos(angle)])


def make_angrad_func(func: Callable) -> Callable:
    """
    Convert parametric equation f(t) -> (x, y) into explicit function f(radius) -> angle. The rad must increase with t.

    Args:
        func: Parametric equation f(t) -> (x, y).

    Returns:
        Explicit function f(radius) -> angle.
    """

    def angrad_func(rad: float, t_min: float, t_max: float, *args, **kwargs) -> tuple[float, float, float, float]:
        """
        Explicit function f(radius) -> angle. It uses iterative algorithm, similar to binary search.

        Args:
            rad: Radial distance.
            t_min: Known minimum.
            t_max: Approximate maximum.
            *args: Other args for func.
            **kwargs: Other kwargs for func.

        Returns:
            np.float64: Angle in radians from -pi to pi.
        """
        is_t_inv = t_max < t_min

        # Select next range if the value is still beyond
        while np.linalg.norm(func(t_max, *args, **kwargs)) < rad:  # type: ignore[attr-defined]
            t_min, t_max = t_max, t_max + (t_max - t_min) * 2

        # Iteratively narrow the range of t until r matches
        for _ in range(100):
            t_curr = np.mean(cast(npt.NDArray, [t_min, t_max]))
            x, y = func(t_curr, *args, **kwargs)
            r_curr = np.linalg.norm([x, y])  # type: ignore[attr-defined]
            if r_curr == rad or not ((t_min > t_curr > t_max) if is_t_inv else (t_min < t_curr < t_max)):
                break
            if r_curr < rad:
                t_min = t_curr
            else:
                t_max = t_curr
        else:
            print('WARNING! angrad_func: Number of iteration exceeded the limit.')

        ang = np.arctan2(y, x)  # Compute angle
        return ang, x, y, t_curr

    return angrad_func


def equidistant(func: Callable, t_lims: tuple[float, float], step: float, tolerance: float, *args, **kwargs) -> (
        npt.NDArray):
    """
    Distributes points evently within the given limits. Adjusts the numer of points to get the desired distance between
    them.

    Args:
        func: Parametric function of the curve.
        t_lims: Top and bottom limits of the parametr t.
        step: Desired distance between points.
        tolerance: Desired accuracy of interpoint distance.
        *args: Parameters of the func.
        **kwargs: Parameters of the func.

    Returns:
        Array of t params.
    """
    t_st, t_en = t_lims
    seg_num = 8
    t_step = (t_en - t_st) / seg_num
    t_range = np.append(np.arange(t_st, t_en, t_step)[:seg_num], t_en)

    for i in range(10):
        points: npt.NDArray = func(t_range, *args, **kwargs)
        transposed_points = np.transpose(points)
        xy_difs = transposed_points[1:] - transposed_points[:-1]
        dists = [np.linalg.norm(xy_dif) for xy_dif in xy_difs]  # type: ignore[attr-defined]
        if np.all(np.absolute((np.array(dists) - step) / step) <= tolerance):  # Check inaccuracy against tolerance
            break
        cum_dists = np.cumsum([0] + dists)
        dist_t_interp_func = interp1d(cum_dists, t_range, kind='linear')
        total_dist = cum_dists[-1]
        seg_num = int(np.ceil(total_dist / step))
        dist_step = total_dist / seg_num
        dist_range = np.arange(dist_step, total_dist, dist_step)[:seg_num - 1]
        t_range = np.concatenate(([t_st], dist_t_interp_func(dist_range), [t_en]))
    else:
        print('WARNING! equidistant: Number of iteration exceeded the limit.')

    return points


def populate_circ(in_x: npt.NDArray, in_y: npt.NDArray, num: int) -> npt.NDArray:
    """
    Multiply points and place them around the origin.

    Args:
        in_x: Points, x values.
        in_y: Points, y values.
        num: Number of copies, including the original one.

    Returns:
        Resulting x and y values respectively.
    """
    angle_step = 2 * np.pi / num
    curves = [rotate(in_x, in_y, angle_step * i) for i in range(num)]
    return stack_curves(*curves)
