from tkinter import *
import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
# import matplotlib
import numpy as np
from PIL import Image, ImageTk



class GearsApp(Tk):
    """Gears app with GUI"""
    def __init__(self):
        super().__init__()

        # Window setup
        self.title('GEARS')
        self.geometry('1000x600')
        self.configure(bg="red")
        self.resizable(True, True)
        self.style = ttk.Style()
        self.style.theme_use('classic')

        # Frames
        main_frame = Frame(self)
        main_frame.pack(padx=4, side=LEFT, fill=BOTH, expand=True)

        # Sidebar
        tabs_frame = Frame(main_frame)
        tabs_frame.pack(side=LEFT, fill=Y)

        self.some_lbl = Label(tabs_frame, text='Some label')
        self.some_lbl.pack(side=TOP)

        self.some_btn = Button(tabs_frame, command=self.button_cmd, text='Some button')
        self.some_btn.pack(side=TOP)

        # style.configure('TButton', background='green')
        self.style.configure('My.TButton', background='red', foreground='green', width=30, height=20, borderwidth=3, focusthickness=10,
                        focuscolor='blue')
        self.extra_btn = ttk.Button(tabs_frame, command=self.button_cmd, text='Extra button', style='My.TButton')
        self.extra_btn.pack(side=TOP)

        # Plots frame
        plots_frame = Frame(main_frame)
        plots_frame.pack(side=LEFT, fill=BOTH, expand=True)


        self.style.configure('Clr.TLabelframe', background='green')

        self.globplot_frame = ttk.LabelFrame(plots_frame, labelwidget=Label(plots_frame, text='Historical data',
                                                                       font=('Times', 10, 'italic')), labelanchor=N, style='Clr.TLabelframe')
        self.globplot_frame.pack(padx=2, pady=2, fill=BOTH, expand=True)

        # Canvas
        self.fig = Figure(figsize=(10, 8))
        self.fig.set_tight_layout(True)
        self.ax = self.fig.add_subplot()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.globplot_frame)
        self.data, = self.ax.plot([], [], color='b', linewidth=1)
        self.plot_data([0, 1.2, 1.8, 3], [0, 0.8, 2.2, 3])

        # Toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.globplot_frame, pack_toolbar=False)
        self.toolbar.pack(side=BOTTOM, padx=2, pady=2, fill=X)

        # Canvas
        self.canvas.get_tk_widget().pack(side=TOP, padx=2, pady=2, fill=BOTH, expand=1)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)

    # Matplotlib functions
    def on_key_press(self, event):
        key_press_handler(event, self.canvas, self.toolbar)

    def plot_data(self, x_vals, y_vals):
        self.data.set_xdata(np.array(x_vals))
        self.data.set_ydata(np.array(y_vals))
        self.ax.relim()  # Recompute the ax.dataLim
        self.ax.autoscale_view()  # Update ax.viewLim using the new dataLim
        self.canvas.draw()

    def button_cmd(self):
        print('Click!')


if __name__ == '__main__':
    gears_app = GearsApp()
    gears_app.mainloop()
    