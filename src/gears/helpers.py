import re
from typing import cast
from typing import Generic
from typing import Type
from typing import TypeVar

import numpy as np
import numpy.typing as npt

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


def sci_round(num: float, sig_fig: int = 1) -> float:
    """
    Scientific round.

    Args:
        num: Number to round.
        sig_fig: Number of significant digits.

    Returns:
        Rounded number.
    """
    return float(f'{num:.{sig_fig - 1}e}')


def round_float_only(val: T, sig_fig: int = 1) -> T:
    """
    Rounds only the float type.

    Args:
        val: Number to round.
        sig_fig: Number of significant digits.

    Returns:
        Rounded number.
    """
    return cast(T, sci_round(val, sig_fig)) if isinstance(val, float) else val


def indentate(text: str) -> str:
    """
    Indentate given text by 1 tab.

    Args:
        text: Multiline text.

    Returns:
        Indented text.
    """
    return re.sub(r'^', '\t', text, flags=re.M)


def replace_batch(text: str, rep_tab: list[tuple[str, str]]) -> str:
    for old, new in rep_tab:
        text = text.replace(old, new)
    return text


def bool_to_sign(bool_val: bool | int) -> int:
    """
    Turns bool value into sign.

    Args:
        bool_val: Can be True, False, 0 or 1

    Returns:
        1 if bool_val = True, else -1
    """
    return bool_val * 2 - 1


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
