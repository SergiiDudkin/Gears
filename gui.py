from tkinter import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.pyplot import Circle
import numpy as np
import os
from tooth_profile import HalfTooth, GearSector
from transforms import upd_xy_lims, merge_xy_lims
from enum import Enum, auto


class State(Enum):
    PAUSE = auto()
    RESUME = auto()
    RESET = auto()
    PLAY = auto()


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
        self.stop_btn = self._Button(text=None, image_file=self.stop_img, toggle=False, command=callback_stop)
        self.cnt_lbl = Label(self, font=self._label_font, width=4, anchor=W)
        self.cnt_lbl.pack(padx=0, pady=0, side=LEFT)

        self.reset_state()

    def set_btn_img(self, btn, img):
        btn._image_file = img
        ToolbarPlayer._set_image_for_button(self, btn)

    def pause_state(self):
        self.play_btn.config(command=self.callback_resume)
        self.set_btn_img(self.play_btn, self.play_img)
        self.next_btn.config(state=NORMAL)
        self.state = State.PAUSE

    def resume_state(self):
        self.next_btn.config(state=DISABLED)
        self.play_btn.config(command=self.callback_pause)
        self.set_btn_img(self.play_btn, self.pause_img)
        self.state = State.RESUME

    def reset_state(self):
        self.play_btn.config(command=self.callback_play)
        self.set_btn_img(self.play_btn, self.play_img)
        self.stop_btn.config(state=DISABLED)
        self.next_btn.config(state=DISABLED)
        self.cnt_lbl['text'] = ''
        self.state = State.RESET

    def play_state(self):
        self.stop_btn.config(state=NORMAL)
        self.play_btn.config(command=self.callback_pause)
        self.set_btn_img(self.play_btn, self.pause_img)
        self.state = State.PLAY

    def upd_frame_num(self, num):
        self.cnt_lbl['text'] = f'#{num}'

    def activate(self):
        if self.state == State.RESET:
            self.play_btn.config(state=NORMAL)

    def deactivate(self):
        if self.state == State.RESET:
            self.play_btn.config(state=DISABLED)


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
        common_params_frame = LabelFrame(self, labelwidget=Label(self, text='Common', font=('Times', 10, 'italic')),
                                         labelanchor=N)
        common_params_frame.pack(side=TOP, padx=2, pady=2, fill=X)
        common_params_frame.columnconfigure(0, weight=1)

        Label(common_params_frame, text='Module').grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.module = EntryValid(common_params_frame, check_pos_finite, width=6, justify='right')
        self.module.grid(row=0, column=1, padx=2, pady=2, sticky=E)
        self.module.insert(END, '10')

        Label(common_params_frame, text='Pressure angle').grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.pressure_angle = EntryValid(common_params_frame, check_90_deg, width=6, justify='right')
        self.pressure_angle.grid(row=1, column=1, padx=2, pady=2, sticky=E)
        self.pressure_angle.insert(END, '20')

        Label(common_params_frame, text='Second gear').grid(row=2, column=0, padx=2, pady=2, sticky=W)
        self.has_gear1 = IntVar()
        self.gear1_cb = Checkbutton(common_params_frame, variable=self.has_gear1, selectcolor='lemon chiffon')
        self.gear1_cb.grid(row=2, column=1, padx=2, pady=2, sticky=E)
        self.has_gear1.trace('w', self.checkbtn_callback)

            # Gear 1
        params0_frame = LabelFrame(self, labelwidget=Label(self, text='Gear 1', font=('Times', 10, 'italic')),
                                   labelanchor=N)
        params0_frame.pack(side=TOP, padx=2, pady=2, fill=X)
        params0_frame.columnconfigure(0, weight=1)

        Label(params0_frame, text='Number of teeth').grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.tooth_num0 = EntryValid(params0_frame, check_pos_int, width=6, justify='right')
        self.tooth_num0.grid(row=0, column=1, padx=2, pady=2, sticky=E)
        self.tooth_num0.insert(END, '40')

        Label(params0_frame, text='Addendum').grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.ad_coef0 = EntryValid(params0_frame, check_pos_finite, width=6, justify='right')
        self.ad_coef0.grid(row=1, column=1, padx=2, pady=2, sticky=E)
        self.ad_coef0.insert(END, '1')

        Label(params0_frame, text='Dedendum').grid(row=2, column=0, padx=2, pady=2, sticky=W)
        self.de_coef0 = EntryValid(params0_frame, check_pos_finite, width=6, justify='right')
        self.de_coef0.grid(row=2, column=1, padx=2, pady=2, sticky=E)
        self.de_coef0.insert(END, '1')

            # Gear 2
        params1_frame = LabelFrame(self, labelwidget=Label(self, text='Gear 2', font=('Times', 10, 'italic')),
                                   labelanchor=N)
        params1_frame.pack(side=TOP, padx=2, pady=2, fill=X)
        params1_frame.columnconfigure(0, weight=1)

        Label(params1_frame, text='Number of teeth').grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.tooth_num1 = EntryValid(params1_frame, check_pos_int, width=6, justify='right')
        self.tooth_num1.grid(row=0, column=1, padx=2, pady=2, sticky=E)
        self.tooth_num1.insert(END, '40')

        Label(params1_frame, text='Addendum').grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.ad_coef1 = EntryValid(params1_frame, check_pos_finite, width=6, justify='right')
        self.ad_coef1.grid(row=1, column=1, padx=2, pady=2, sticky=E)
        self.ad_coef1.insert(END, '1')

        Label(params1_frame, text='Dedendum').grid(row=2, column=0, padx=2, pady=2, sticky=W)
        self.de_coef1 = EntryValid(params1_frame, check_pos_finite, width=6, justify='right')
        self.de_coef1.grid(row=2, column=1, padx=2, pady=2, sticky=E)
        self.de_coef1.insert(END, '1')

        self.input_fields = get_entry_valid_recur(self)
        self.gear1_inputs = get_entry_valid_recur(params1_frame)
        self.checkbtn_callback()

    def input_callback(self):
        if self.input_fields:
            if all([field.is_valid for field in self.input_fields]):
                self.master.master.toolbar.activate()
            else:
                self.master.master.toolbar.deactivate()

    def checkbtn_callback(self, *args):
        state = NORMAL if self.has_gear1.get() else DISABLED
        for input_field in self.gear1_inputs:
            input_field.config(state=state)


class GearsApp(Tk):
    """Gears app with GUI"""
    def __init__(self):
        super().__init__()

        # Window setup
        self.title('GEARS')
        self.geometry('1000x800')
        self.resizable(True, True)

        # Frames
        main_frame = Frame(self)
        main_frame.pack(padx=2, pady=2, side=LEFT, fill=BOTH, expand=True)

        # Sidebar
        self.inputs = InputFrame(main_frame)

            # Plots frame
        plots_frame = Frame(main_frame)
        plots_frame.pack(side=LEFT, fill=BOTH, expand=True)
        self.globplot_frame = LabelFrame(plots_frame, labelwidget=Label(plots_frame, text='Simulation',
                                         font=('Times', 10, 'italic')), labelanchor=N)
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
        self.canvas.get_tk_widget().pack(side=TOP, padx=0, pady=1, fill=BOTH, expand=1)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)

        self.inputs.input_callback()
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
        self.toolbar.play_state()
        module = float(self.inputs.module.strvar.get())
        pressure_angle = np.deg2rad(float(self.inputs.pressure_angle.strvar.get()))
        self.tooth0 = HalfTooth(tooth_num=int(self.inputs.tooth_num0.strvar.get()),
                                module=module,
                                pressure_angle=pressure_angle,
                                ad_coef=float(self.inputs.ad_coef0.strvar.get()),
                                de_coef=float(self.inputs.de_coef0.strvar.get()))

        # self.tooth1 = HalfTooth(tooth_num=61, module=module, pressure_angle=pressure_angle, de_coef=1)
        self.tooth1 = HalfTooth(tooth_num=int(self.inputs.tooth_num1.strvar.get()),
                                module=module,
                                pressure_angle=pressure_angle,
                                ad_coef=float(self.inputs.ad_coef1.strvar.get()),
                                de_coef=float(self.inputs.de_coef1.strvar.get()))

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
        self.toolbar.pause_state()

    def resume(self, event=None):
        self.toolbar.resume_state()
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
        self.toolbar.reset_state()


if __name__ == '__main__':
    gears_app = GearsApp()
    gears_app.mainloop()
    