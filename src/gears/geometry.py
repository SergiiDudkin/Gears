import numpy as np
import numpy.typing as npt


def linecirc_intersec(x1: float, y1: float, x2: float, y2: float, cntr_x: float, cntr_y: float, radlen: float) -> (
        tuple[float, float] | tuple[float, float, float, float]):
    """
    Find intersection of line and circle (http://mathworld.wolfram.com/Circle-LineIntersection.html)

    Args:
        x1: Line, point 1 x.
        y1: Line, point 1 y.
        x2: Line, point 2 x.
        y2: Line, point 2 y.
        cntr_x: Circle center x.
        cntr_y: Circle center y.
        radlen: Radius of the circle.

    Returns:
        One tangent point or two points of intersection.

    Raises:
        RuntimeError: Line and circumference does not have common points.
    """
    dx = x2 - x1
    dy = y2 - y1
    dr = np.linalg.norm([dx, dy])  # type: ignore[attr-defined]
    D = np.linalg.det(np.array([[x1 - cntr_x, x2 - cntr_x], [y1 - cntr_y, y2 - cntr_y]]))  # type: ignore[attr-defined]
    dr2 = np.square(dr)
    discriminant = np.square(radlen) * dr2 - np.square(D)
    sgn = -1 if dy < 0 else 1
    if discriminant > 0:
        x3 = (D * dy + sgn * dx * np.sqrt(discriminant)) / dr2 + cntr_x
        y3 = (- D * dx + abs(dy) * np.sqrt(discriminant)) / dr2 + cntr_y
        x4 = (D * dy - sgn * dx * np.sqrt(discriminant)) / dr2 + cntr_x
        y4 = (- D * dx - abs(dy) * np.sqrt(discriminant)) / dr2 + cntr_y
        return x3, y3, x4, y4
    elif discriminant == 0:
        x3 = D * dy / dr2 + cntr_x
        y3 = - D * dx / dr2 + cntr_y
        return x3, y3
    else:
        raise RuntimeError('No line-circumference intersection!')


def lineline_intersec(x1: float, y1: float, x2: float, y2: float,
                      x3: float, y3: float, x4: float, y4: float) -> tuple[float, float]:
    """
    Find intersection of two lines.

    The lines are defined as non-zero length non-parallel segments.

    Args:
        x1: Segment A, point 1, x.
        y1: Segment A, point 1, y.
        x2: Segment A, point 2, x.
        y2: Segment A, point 2, y.
        x3: Segment B, point 1, x.
        y3: Segment B, point 1, y.
        x4: Segment B, point 2, x.
        y4: Segment B, point 2, y.

    Returns:
        Point of intersection.

    Raises:
        RuntimeError: No intersection point.
    """
    a = x1 * y2 - y1 * x2
    b = x3 - x4
    c = x1 - x2
    d = x3 * y4 - y3 * x4
    e = y3 - y4
    f = y1 - y2
    g = c * e - f * b
    if g == 0:
        raise RuntimeError('Parallel lines or zero length segment(s)!')
    ipoi_y = (a * e - f * d) / g  # Intersection point, x value
    ipoi_x = (a * b - c * d) / g  # Intersection point, y value
    return ipoi_x, ipoi_y


def get_unit_vector(vec: npt.NDArray) -> npt.NDArray:
    return vec / np.linalg.norm(vec)  # type: ignore[attr-defined]


def is_within_ang(q_ang: float, st_ang: float, en_ang: float) -> bool:
    operator = np.bitwise_and if st_ang < en_ang else np.bitwise_or
    return operator(st_ang <= q_ang, q_ang < en_ang)  # type: ignore[operator]


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
