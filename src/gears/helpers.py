import re
from numbers import Number


def sci_round(num: Number, sig_fig: int = 1) -> float:
    return float(f'{num:.{sig_fig - 1}e}')


def indentate(text: str) -> str:
    return re.sub(r'^', '\t', text, flags=re.M)
