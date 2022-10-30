from matplotlib import pyplot as plt


def simple_plot(x_vals, y_vals, title='Figure 1'):
    # Build plot
    plt.plot(x_vals, y_vals, color='b', linewidth=0.5)
    plt.get_current_fig_manager().set_window_title(title)
    fig = plt.figure(1)
    fig.set_tight_layout(True)
    ax = fig.axes[0]
    ax.set_aspect('equal', 'box')
    plt.show()


def multiple_plot(data):
    # Build plot
    for (x_vals, y_vals), label in data:
        plt.plot(x_vals, y_vals, linewidth=1, label=label)
    plt.legend(loc='best', fancybox=False, fontsize='medium')
    fig = plt.figure(1)
    fig.set_tight_layout(True)
    ax = fig.axes[0]
    ax.set_aspect('equal', 'box')
    plt.show()
