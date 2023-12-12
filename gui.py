from tkinter import *
import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.pyplot import Circle
import numpy as np
import os
from tooth_profile import HalfTooth, GearSector
from transforms import upd_xy_lims, merge_xy_lims


class ToolbarPlayer(NavigationToolbar2Tk):
    def __init__(self, canvas, window, callback_play, callback_next_frame, callback_pause, callback_resume,
                 callback_stop):
        self.callback_play = callback_play
        self.callback_pause = callback_pause
        self.callback_resume = callback_resume

        super().__init__(canvas, window, pack_toolbar=False)
        self.pack(side=BOTTOM, padx=2, pady=0, fill=X)
        self._Spacer()

        self.script_folder = os.path.dirname(os.path.realpath(__file__))
        self.play_img = os.path.join(self.script_folder, 'images', 'play.png')
        self.stop_img = os.path.join(self.script_folder, 'images', 'stop.png')
        self.pause_img = os.path.join(self.script_folder, 'images', 'pause.png')
        self.next_img = os.path.join(self.script_folder, 'images', 'next.png')

        self.play_btn = self._Button(text=None, image_file=self.play_img, toggle=False, command=callback_play)
        self.next_btn = self._Button(text=None, image_file=self.next_img, toggle=False, command=callback_next_frame)
        self.next_btn.config(state=DISABLED)
        self.stop_btn = self._Button(text=None, image_file=self.stop_img, toggle=False, command=callback_stop)
        self.stop_btn.config(state=DISABLED)

        self.cnt_lbl = Label(self, font=self._label_font, width=4, anchor=W)
        self.cnt_lbl.pack(padx=2, pady=0, side=LEFT)

    def set_btn_img(self, btn, img):
        btn._image_file = img
        ToolbarPlayer._set_image_for_button(self, btn)

    def pause_cfg(self):
        self.play_btn.config(command=self.callback_resume)
        self.set_btn_img(self.play_btn, self.play_img)
        self.next_btn.config(state=NORMAL)

    def resume_cfg(self):
        self.next_btn.config(state=DISABLED)
        self.play_btn.config(command=self.callback_pause)
        self.set_btn_img(self.play_btn, self.pause_img)

    def reset_cfg(self):
        self.play_btn.config(command=self.callback_play)
        self.set_btn_img(self.play_btn, self.play_img)
        self.stop_btn.config(state=DISABLED)
        self.next_btn.config(state=DISABLED)
        self.cnt_lbl['text'] = ''

    def play_cfg(self):
        self.stop_btn.config(state=NORMAL)
        self.play_btn.config(command=self.callback_pause)
        self.set_btn_img(self.play_btn, self.pause_img)

    def upd_frame_num(self, num):
        self.cnt_lbl['text'] = f'#{num}'


class GearsApp(Tk):
    """Gears app with GUI"""
    def __init__(self):
        super().__init__()

        # Window setup
        self.title('GEARS')
        self.geometry('800x800')
        self.resizable(True, True)
        self.style = ttk.Style()
        self.style.theme_use('classic')

        # Frames
        main_frame = Frame(self)
        main_frame.pack(padx=2, pady=2, side=LEFT, fill=BOTH, expand=True)

            # Plots frame
        plots_frame = Frame(main_frame)
        plots_frame.pack(side=LEFT, fill=BOTH, expand=True)
        self.globplot_frame = ttk.LabelFrame(plots_frame, labelwidget=Label(plots_frame, text='2D Model',
                                             font=('Times', 10, 'italic')), labelanchor=N, style='Clr.TLabelframe')
        self.globplot_frame.pack(padx=2, pady=2, ipady=0, fill=BOTH, expand=True)

                # Matplotlib canvas
        self.fig = Figure(figsize=(10, 8))
        self.fig.set_tight_layout(True)
        self.fig.set_facecolor(self.cget("background"))
        self.ax = self.fig.add_subplot()
        self.ax.set_aspect('equal', 'box')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.globplot_frame)
        self.ax.plot([], [], color='b', linewidth=1)
        self.ax.plot([], [], color='r', linewidth=1)
        self.ax.set_xlim((0, 1))
        self.ax.set_ylim((0, 1))
        self.toolbar = ToolbarPlayer(self.canvas, self.globplot_frame, self.play, self.next_frame, self.pause,
                                     self.resume, self.stop)
        self.canvas.get_tk_widget().pack(side=TOP, padx=2, pady=0, fill=BOTH, expand=1)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)

        self.tooth0 = HalfTooth(tooth_num=18, module=10, de_coef=1)
        self.tooth1 = HalfTooth(tooth_num=61, module=10, de_coef=1)
        self.delay_ms = 1
        self.after_id = None
        self.has_gear0 = True
        self.has_gear1 = True

    # Matplotlib funcs
    def on_key_press(self, event):
        key_press_handler(event, self.canvas, self.toolbar)

    def plot_data(self, line, x_vals, y_vals):
        line.set_xdata(np.array(x_vals))
        line.set_ydata(np.array(y_vals))
        self.ax.relim()  # Recompute the ax.dataLim
        self.ax.autoscale_view()  # Update ax.viewLim using the new dataLim
        self.canvas.draw()

    # Button callbacks
    def play(self, event=None):
        self.break_loop()
        self.toolbar.play_cfg()
        xy_lims = (float('inf'), float('inf'), float('-inf'), float('-inf'))

        if self.has_gear0:
            self.gear_sector0 = GearSector(self.tooth0, self.tooth0, step_cnt=100, sector=(np.pi*1.75, np.pi*0.25),
                                           rot_ang=0, is_acw=False)
            self.rotating_gear_sector0 = iter(self.gear_sector0)
            ctr_circ = Circle((0, 0), self.gear_sector0.ht0.pitch_radius * 0.01, color='b')
            self.ax.add_patch(ctr_circ)
            xy_lims = merge_xy_lims(*xy_lims, *self.gear_sector0.get_limits())
            xy_lims = upd_xy_lims(0, 0, *xy_lims)

        if self.has_gear1:
            self.gear_sector1 = GearSector(self.tooth1, self.tooth1, step_cnt=100, sector=(np.pi*0.75, np.pi*1.25),
                                           rot_ang=np.pi, is_acw=True)
            self.rotating_gear_sector1 = iter(self.gear_sector1)
            self.ctr_dist = self.gear_sector0.ht0.pitch_radius + self.gear_sector1.ht0.pitch_radius
            ctr_circ = Circle((self.ctr_dist, 0), self.gear_sector1.ht0.pitch_radius * 0.01, color='r')
            self.ax.add_patch(ctr_circ)
            xy_lims_ = self.gear_sector1.get_limits()
            xy_lims = merge_xy_lims(*xy_lims, xy_lims_[0] + self.ctr_dist, xy_lims_[1], xy_lims_[2] + self.ctr_dist,
                                    xy_lims_[3])
            xy_lims = upd_xy_lims(self.ctr_dist, 0, *xy_lims)

        min_x, min_y, max_x, max_y = xy_lims
        margin = max(max_x - min_x, max_y - min_y) * 0.05
        self.ax.set_xlim((min_x - margin, max_x + margin))
        self.ax.set_ylim((min_y - margin, max_y + margin))

        self.show_next_frame()

    def next_frame(self):
        self.show_next_frame()
        self.break_loop()

    def pause(self, event=None):
        self.break_loop()
        self.toolbar.pause_cfg()

    def resume(self, event=None):
        self.toolbar.resume_cfg()
        self.show_next_frame()

    def stop(self):
        self.break_loop()
        self.reset()

    # Helpers
    def show_next_frame(self):
        if self.has_gear0:
            self.plot_data(self.ax.lines[0], *next(self.rotating_gear_sector0))
        if self.has_gear1:
            x_es, y_es = next(self.rotating_gear_sector1)
            self.plot_data(self.ax.lines[1], x_es + self.ctr_dist, y_es)
        self.toolbar.upd_frame_num(self.gear_sector0.i)
        self.after_id = self.after(self.delay_ms, self.show_next_frame)

    def break_loop(self):
        """Stop circulating frames"""
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None

    def reset(self):
        """Restore initial appearance"""
        [patch.remove() for patch in self.ax.patches]
        [self.plot_data(line, [], []) for line in self.ax.lines]
        self.toolbar.reset_cfg()


if __name__ == '__main__':
    gears_app = GearsApp()
    gears_app.mainloop()
    