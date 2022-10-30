import numpy as np


def mirror(poi, seg_st, seg_en):
    """
    Reflect the point relative to the mirror line. It is XY-invariant.

    Args:
        poi (np.ndarray): Point to be reflected.
        seg_st (np.ndarray): First point of the mirror line
        seg_en (np.ndarray): Second point of the mirror line

    Returns:
        np.ndarray: Reflected point.
    """
    seg = seg_en - seg_st  # The segment vector
    proj_poi = seg_st + seg * np.vdot(seg, poi - seg_st) / np.vdot(seg, seg)  # Point of projection
    mirror_poi = proj_poi * 2 - poi  # Reflected point
    return mirror_poi


def rotate(x, y, angle):
    """Rotate points around the origin."""
    return x * np.cos(angle) - y * np.sin(angle), x * np.sin(angle) + y * np.cos(angle)


def angle_vec(vec0, vec1):  # Not tested! Not used here!
    y = np.linalg.det(np.vstack((vec0, vec1)))
    x = np.sum(vec0 * vec1)
    return np.arctan2(y, x)


def cartesian_to_polar(x, y):  # Not used here!
    ang = np.arctan2(y, x)
    rad = np.linalg.norm([x, y])
    return ang, rad


def make_angrad_func(func):
    """
    Convert parametric equation f(t) -> (x, y) into explicit function f(radius) -> angle. The rad must increase with t.

    Args:
        func (Callable): Parametric equation f(t) -> (x, y).

    Returns:
        Callable: Explicit function f(radius) -> angle.
    """

    def angrad_func(rad, t_min, t_max, *args, **kwargs):
        """
        Explicit function f(radius) -> angle. It uses iterative algorithm, similar to binary search.

        Args:
            r (float): Radial distance.
            t_min (float): Known minimum.
            t_max (float): Approximate maximum.
            *args: Other args for func.
            **kwargs: Other kwargs for func.

        Returns:
            np.float64: Angle in radians from -pi to pi.
        """

        # Select next range if the value is still beyond
        while np.linalg.norm(func(t_max, *args, **kwargs)) < rad:
            t_min, t_max = t_max, t_max + (t_max - t_min) * 2

        # Iteratively narrow the range of t until r matches
        for _ in range(100):
            t_curr = np.mean([t_min, t_max])
            x, y = func(t_curr, *args, **kwargs)
            r_curr = np.linalg.norm([x, y])
            # print(f't_curr {t_curr}, r_curr {r_curr}, x {x}, y{y}')
            if r_curr == rad or not (t_min < t_curr < t_max):
                break
            if r_curr < rad:
                t_min = t_curr
            else:
                t_max = t_curr
        else:
            print('WARNING! Number of iteration exceeded the limit.')
        # print(args)
        # print(kwargs)

        ang = np.arctan2(y, x)  # Compute angle
        return ang, x, y, t_curr

    return angrad_func


def populate_circ(in_x, in_y, num):
    """
    Multiply points and place them around the origin.

    Args:
        in_x (np.ndarray): Points, x values.
        in_y (np.ndarray): Points, y values.
        num (int): Number of copies, including the original one.

    Returns:
        tuple[np.ndarray, np.ndarray]: Resulting x and y values respectively.
    """
    angle_step = 2 * np.pi / num
    out_x, out_y = in_x, in_y
    for i in range(1, num):
        angle_step * i
        new_x, new_y = rotate(in_x, in_y, angle_step * i)
        out_x = np.concatenate((out_x, new_x))
        out_y = np.concatenate((out_y, new_y))
    return out_x, out_y
