import re
from numbers import Number

import numpy as np


def sci_round(num: Number, sig_fig: int = 1) -> float:
    return float(f'{num:.{sig_fig - 1}e}')


def indentate(text: str) -> str:
    return re.sub(r'^', '\t', text, flags=re.M)


def linecirc_intersec(x1, y1, x2, y2, cntr_x, cntr_y, radlen):
    """Find intersection of line and circle (http://mathworld.wolfram.com/Circle-LineIntersection.html)"""
    dx = x2 - x1
    dy = y2 - y1
    dr = np.linalg.norm([dx, dy])
    # cntr_y, cntr_x = cntr
    D = np.linalg.det(np.array([[x1 - cntr_x, x2 - cntr_x], [y1 - cntr_y, y2 - cntr_y]]))
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
        return 'No intersection!'
