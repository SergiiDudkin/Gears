import re


def sci_round(num, sig_fig=1):
    return float(f'{num:.{sig_fig - 1}e}')


def indentate(text):
    return re.sub(r'^', '\t', text, flags=re.M)
