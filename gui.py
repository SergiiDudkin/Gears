from tkinter import *
import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
# import matplotlib
import numpy as np
from PIL import Image, ImageTk
import os
from tooth_profile import HalfTooth, GearSector



class GearsApp(Tk):
    """Gears app with GUI"""
    def __init__(self):
        super().__init__()

        # Window setup
        self.title('GEARS')
        self.geometry('1000x600')
        self.resizable(True, True)
        self.style = ttk.Style()
        self.style.theme_use('classic')

        # Frames
        main_frame = Frame(self)
        main_frame.pack(padx=4, side=LEFT, fill=BOTH, expand=True)

            # Buttons frame
        self.btnpanel = Frame(main_frame)
        self.btnpanel.pack(padx=2, pady=2, fill=X, side=BOTTOM)

        self.script_folder = os.path.dirname(os.path.realpath(__file__))
        self.play_img = PhotoImage(file=os.path.join(self.script_folder, 'images', 'play.png'))
        self.stop_img = PhotoImage(file=os.path.join(self.script_folder, 'images', 'stop.png'))
        self.pause_img = PhotoImage(file=os.path.join(self.script_folder, 'images', 'pause.png'))
        self.next_img = PhotoImage(file=os.path.join(self.script_folder, 'images', 'next.png'))

        self.cnt_lbl = Label(self.btnpanel, font='"Courier New" 16', bg='white', width=4, anchor=E)
        self.cnt_lbl.pack(padx=2, pady=0, side=RIGHT)
        self.stop_btn = Button(self.btnpanel, image=self.stop_img, command=self.stop, state=DISABLED)
        self.stop_btn.pack(padx=0, pady=0, side=RIGHT)
        self.next_btn = Button(self.btnpanel, image=self.next_img, command=self.next_frame, state=DISABLED)
        self.next_btn.pack(padx=0, pady=0, side=RIGHT)
        self.play_btn = Button(self.btnpanel, image=self.play_img, command=self.play, state=NORMAL)
        self.play_btn.pack(padx=0, pady=0, side=RIGHT)


            # Plots frame
        plots_frame = Frame(main_frame)
        plots_frame.pack(side=LEFT, fill=BOTH, expand=True)
        self.globplot_frame = ttk.LabelFrame(plots_frame, labelwidget=Label(plots_frame, text='Historical data',
                                             font=('Times', 10, 'italic')), labelanchor=N, style='Clr.TLabelframe')
        self.globplot_frame.pack(padx=2, pady=2, fill=BOTH, expand=True)

                # Canvas
        self.fig = Figure(figsize=(10, 8))
        self.fig.set_tight_layout(True)
        self.ax = self.fig.add_subplot()
        self.ax.set_aspect('equal', 'box')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.globplot_frame)
        self.data, = self.ax.plot([], [], color='b', linewidth=1)
        self.ax.set_xlim((0, 1))
        self.ax.set_ylim((0, 1))

                # Toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.globplot_frame, pack_toolbar=False)
        self.toolbar.pack(side=BOTTOM, padx=2, pady=2, fill=X)

                # Canvas
        self.canvas.get_tk_widget().pack(side=TOP, padx=2, pady=2, fill=BOTH, expand=1)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)


        self.tooth = HalfTooth(tooth_num=18, module=10, de_coef=1)
        # self.tooth()
        self.delay_ms = 1
        self.after_id = None


    # Matplotlib functions
    def on_key_press(self, event):
        key_press_handler(event, self.canvas, self.toolbar)

    def plot_data(self, x_vals, y_vals):
        self.data.set_xdata(np.array(x_vals))
        self.data.set_ydata(np.array(y_vals))
        self.ax.relim()  # Recompute the ax.dataLim
        self.ax.autoscale_view()  # Update ax.viewLim using the new dataLim
        self.canvas.draw()



    def pause(self, event=None):
        self.break_loop()
        self.play_btn.config(image=self.play_img, command=self.resume)
        self.next_btn.config(state=NORMAL)

    def resume(self, event=None):
        self.next_btn.config(state=DISABLED)
        self.show_next_frame()
        self.play_btn.config(image=self.pause_img, command=self.pause)

    def break_loop(self):
        """Stop circulating frames"""
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None



    def stop(self):
        self.break_loop()
        self.reset()

    def reset(self):
        self.play_btn.config(image=self.play_img, command=self.play)
        self.plot_data([], [])
        self.stop_btn.config(state=DISABLED)
        self.next_btn.config(state=DISABLED)
        self.cnt_lbl['text'] = ''

    def next_frame(self):
        self.show_next_frame()
        self.break_loop()

    def play(self, event=None):
        self.stop_btn.config(state=NORMAL)
        self.break_loop()
        self.play_btn.config(image=self.pause_img, command=self.pause)
        self.gear_sector = GearSector(self.tooth, self.tooth, step_cnt=100, sector=(np.pi/2, np.pi), rot_ang=0,
                                      is_acw=False)
        self.rotating_gear_sector = iter(self.gear_sector)
        self.ax.set_xlim((-105, 5))
        self.ax.set_ylim((-5, 105))
        self.show_next_frame()

    def show_next_frame(self):
        self.plot_data(*next(self.rotating_gear_sector))
        self.cnt_lbl['text'] = self.gear_sector.i
        self.after_id = self.after(self.delay_ms, self.show_next_frame)


if __name__ == '__main__':
    gears_app = GearsApp()
    gears_app.mainloop()
    