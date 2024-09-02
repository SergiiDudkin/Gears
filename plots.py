from typing import Optional

import numpy.typing as npt
from matplotlib import pyplot as plt


def simple_plot(x_vals: npt.ArrayLike, y_vals: npt.ArrayLike, title: str = 'Figure 1', marker: Optional[str] = None,
                markersize: Optional[int] = None) -> None:
    plt.plot(x_vals, y_vals, color='b', linewidth=0.5, marker=marker, markersize=markersize)  # type: ignore[arg-type]
    plt.get_current_fig_manager().set_window_title(title)  # type: ignore[attr-defined]
    fig = plt.figure(1)
    fig.set_tight_layout(True)  # type: ignore[attr-defined]
    ax = fig.axes[0]  # type: ignore[attr-defined]
    ax.set_aspect('equal', 'box')
    plt.show()


def multiple_plot(data: list[tuple[npt.NDArray, str]], title='Figure 1', marker=None, markersize=None) -> None:
    for (x_vals, y_vals), label in data:  # type: ignore[misc]
        plt.plot(x_vals, y_vals, linewidth=1, label=label, marker=marker, markersize=markersize)
    plt.get_current_fig_manager().set_window_title(title)  # type: ignore[attr-defined]
    plt.legend(loc='best', fancybox=False, fontsize='medium')  # type: ignore[attr-defined, call-arg]
    fig = plt.figure(1)
    fig.set_tight_layout(True)  # type: ignore[attr-defined]
    ax = fig.axes[0]  # type: ignore[attr-defined]
    ax.set_aspect('equal', 'box')
    plt.show()
