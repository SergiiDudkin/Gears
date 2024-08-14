import re
from numbers import Number

import numpy as np


def sci_round(num: Number, sig_fig: int = 1) -> float:
    return float(f'{num:.{sig_fig - 1}e}')


def indentate(text: str) -> str:
    return re.sub(r'^', '\t', text, flags=re.M)


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
