from typing import Callable
from typing import cast
from typing import TypeVar

import numpy as np
import numpy.typing as npt
from scipy.interpolate import interp1d  # type: ignore[import-untyped]

ArrOrNumG = TypeVar('ArrOrNumG', np.ndarray, float)


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


def angle_vec(vec0: npt.NDArray, vec1: npt.NDArray) -> npt.NDArray:  # Not used here!
    """
    Returns the angle between two vectors. If the vector 0 is rotated ACW to get the same direction as vector 1, then
    the angle is positive (negative otherwise).

    Args:
        vec0: Radius vector 0
        vec1: Radius vector 1

    Returns:
        Angle between two vectors, in radians. -1 < angle <= 1.
    """
    y = np.linalg.det(np.vstack((vec0, vec1)))  # type: ignore[attr-defined]
    x = np.sum(vec0 * vec1)
    return np.arctan2(y, x)


def cartesian_to_polar(x: ArrOrNumG, y: ArrOrNumG) -> tuple[ArrOrNumG, ArrOrNumG]:
    ang = np.remainder(np.arctan2(y, x), np.pi * 2)
    rad = np.linalg.norm([x, y])  # type: ignore[attr-defined]
    return ang, rad


def polar_to_cartesian(ang: ArrOrNumG, rad: ArrOrNumG) -> tuple[ArrOrNumG, ArrOrNumG]:
    x = rad * np.cos(ang)
    y = rad * np.sin(ang)
    return x, y


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
            print('WARNING! Number of iteration exceeded the limit.')

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
        print('WARNING! Number of iteration exceeded the limit.')

    return points


def stack_curves(*curves) -> npt.NDArray:
    return np.hstack(tuple([line[:, 1:] if idx else line for idx, line in enumerate(curves)]))


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


def is_within_ang(q_ang: float, st_ang: float, en_ang: float) -> bool:
    operator = np.bitwise_and if st_ang < en_ang else np.bitwise_or
    return operator(st_ang <= q_ang, q_ang < en_ang)  # type: ignore[operator]


def upd_xy_lims(x: float, y: float, min_x: float, min_y: float, max_x: float, max_y: float) -> tuple[float, float,
                                                                                                     float, float]:
    min_x = min(min_x, x)
    min_y = min(min_y, y)
    max_x = max(max_x, x)
    max_y = max(max_y, y)
    return min_x, min_y, max_x, max_y


def merge_xy_lims(min_x0: float, min_y0: float, max_x0: float, max_y0: float, min_x1: float, min_y1: float,
                  max_x1: float, max_y1: float) -> tuple[float, float, float, float]:
    return min(min_x0, min_x1), min(min_y0, min_y1), max(max_x0, max_x1), max(max_y0, max_y1)
