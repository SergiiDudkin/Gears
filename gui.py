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

    def activate(self):
        print('activate')

    def deactivate(self):
        print('deactivate')


class EntryValid(Entry, object):
    """General entry widget with validation. Validator func must be added as the 2nd argument."""
    def __init__(self, parent, validator, **kwargs):
        self.input_callback = parent.master.input_callback
        self.validator = validator
        self.strvar = StringVar(parent)
        self.strvar.trace('w', self.entry_callback)
        kwargs['textvariable'] = self.strvar
        super().__init__(parent, **kwargs)
        self.entry_callback()

    def entry_callback(self, *args):
        self.is_valid = self.validator(self.strvar.get())
        self['bg'] = 'lemon chiffon' if self.is_valid else '#fca7b8'
        self.input_callback()


def check_pos_int(strvar):
    try:
        num = int(strvar)
    except ValueError:
        return False
    return True if num > 0 else False


def check_pos_finite(strvar):
    try:
        num = float(strvar)
    except ValueError:
        return False
    return True if (num > 0 and num != float('inf')) else False


def check_90_deg(strvar):
    try:
        num = float(strvar)
    except ValueError:
        return False
    return True if (0 < num < 90) else False


def get_entry_valid_recur(widget):
    return [widget] if isinstance(widget, EntryValid) \
        else [item for child in widget.winfo_children() for item in get_entry_valid_recur(child)]


class InputFrame(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(side=LEFT, fill=Y)
        self.input_fields = []

            # Common
        common_params_frame = ttk.LabelFrame(self, labelwidget=Label(self, text='Common',
                                                                     font=('Times', 10, 'italic')),
                                             labelanchor=N, style='Clr.TLabelframe')
        common_params_frame.pack(side=TOP, padx=2, pady=2, fill=X)
        common_params_frame.columnconfigure(0, weight=1)

        Label(common_params_frame, text='Module').grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.module = EntryValid(common_params_frame, check_pos_finite, width=6, justify='right')
        self.module.grid(row=0, column=1, padx=2, pady=2, sticky=E)

        Label(common_params_frame, text='Pressure angle').grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.pressure_angle = EntryValid(common_params_frame, check_90_deg, width=6, justify='right')
        self.pressure_angle.grid(row=1, column=1, padx=2, pady=2, sticky=E)

            # Gear 1
        params0_frame = ttk.LabelFrame(self, labelwidget=Label(self, text='Gear 1',
                                                                     font=('Times', 10, 'italic')),
                                       labelanchor=N, style='Clr.TLabelframe')
        params0_frame.pack(side=TOP, padx=2, pady=2, fill=X)
        params0_frame.columnconfigure(0, weight=1)

        Label(params0_frame, text='Number of teeth').grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.tooth_num0 = EntryValid(params0_frame, check_pos_int, width=6, justify='right')
        self.tooth_num0.grid(row=0, column=1, padx=2, pady=2, sticky=E)

        Label(params0_frame, text='Addendum').grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.addendum0 = EntryValid(params0_frame, check_pos_finite, width=6, justify='right')
        self.addendum0.grid(row=1, column=1, padx=2, pady=2, sticky=E)

        Label(params0_frame, text='Dedendum').grid(row=2, column=0, padx=2, pady=2, sticky=W)
        self.dedendum0 = EntryValid(params0_frame, check_pos_finite, width=6, justify='right')
        self.dedendum0.grid(row=2, column=1, padx=2, pady=2, sticky=E)

        self.input_fields = get_entry_valid_recur(self)

    def input_callback(self):
        if self.input_fields:
            if all([field.is_valid for field in self.input_fields]):
                self.master.master.toolbar.activate()
            else:
                self.master.master.toolbar.deactivate()


class GearsApp(Tk):
    """Gears app with GUI"""
    def __init__(self):
        super().__init__()

        # Window setup
        self.title('GEARS')
        self.geometry('1000x800')
        self.resizable(True, True)
        self.style = ttk.Style()
        self.style.theme_use('classic')

        # Frames
        main_frame = Frame(self)
        main_frame.pack(padx=2, pady=2, side=LEFT, fill=BOTH, expand=True)

        # Sidebar
        self.inputs = InputFrame(main_frame)

            # Plots frame
        plots_frame = Frame(main_frame)
        plots_frame.pack(side=LEFT, fill=BOTH, expand=True)
        self.globplot_frame = ttk.LabelFrame(plots_frame, labelwidget=Label(plots_frame, text='Simulation',
                                             font=('Times', 10, 'italic')), labelanchor=N, style='Clr.TLabelframe')
        self.globplot_frame.pack(padx=2, pady=2, ipady=0, fill=BOTH, expand=True)

                # Matplotlib canvas
        self.fig = Figure(figsize=(10, 8))
        self.fig.set_tight_layout(True)
        self.fig.set_facecolor(self.cget("background"))
        # self.fig.set_facecolor('r')
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

        # self.tooth0 = HalfTooth(tooth_num=18, module=10, de_coef=1)
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
        self.tooth0 = HalfTooth(tooth_num=int(self.inputs.tooth_num0.strvar.get()), module=10, de_coef=float(self.inputs.dedendum0.strvar.get()))
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
    