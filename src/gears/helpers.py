import re
from numbers import Number
from typing import Generic
from typing import Type
from typing import TypeVar

import numpy as np
import numpy.typing as npt


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


def seedrange(st: float, en: float, seed: float, step: float) -> npt.NDArray:
    """
    Generates a range within st and en (both including), where the seed matches the infinite sequence.

    Args:
        st: Start, including.
        en: End, including.
        seed: The mandatory value of sequence.
        step: Difference between adjacent values.

    Returns:
        Range with the given parameters.
    """
    st_ = (seed - st) % step + st
    res = np.arange(st_, en + 0.5 * step, step, dtype=np.float_)
    if res.size and res[-1] > en:
        res = res[:-1]
    return res


def get_unit_vector(vec: npt.NDArray) -> npt.NDArray:
    return vec / np.linalg.norm(vec)  # type: ignore[attr-defined]


def bool_to_sign(bool_val: bool | int) -> int:
    """
    Turns bool value into sign.

    Args:
        bool_val: Can be True, False, 0 or 1

    Returns:
        1 if bool_val = True, else -1
    """
    return bool_val * 2 - 1


T = TypeVar('T')


class Singleton(type, Generic[T]):
    """Singleton meta class"""

    _instances: dict[Type[T], T] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in Singleton._instances:
            Singleton._instances[cls] = super().__call__(*args, **kwargs)
        return Singleton._instances[cls]


class Clock(metaclass=Singleton):
    """Global clock"""

    def __init__(self):
        self.step_cnt = 1
        self.i = 0

    def set_step_cnt(self, step_cnt: int):
        self.step_cnt = step_cnt

    def reset(self):
        self.i = self.step_cnt - 1

    def inc(self):
        self.i = (self.i + 1) % self.step_cnt

    def dec(self):
        self.i = (self.i + self.step_cnt - 1) % self.step_cnt

    @property
    def progress(self):
        return self.i / self.step_cnt
