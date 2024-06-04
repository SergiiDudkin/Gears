from tkinter import *
from tkinter import filedialog
import tkinter.font as tkfont
import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.pyplot import Circle
import numpy as np
import os
from tooth_profile import HalfTooth, GearSector
from transforms import upd_xy_lims, merge_xy_lims
from enum import Enum, auto
from helpers import indentate


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


class EntryValid(Entry):
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


class SpinboxValid(Spinbox):
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


def check_float(strvar):
    try:
        float(strvar)
        return True
    except ValueError:
        return False


def check_abs_one(strvar):
    try:
        num = float(strvar)
    except ValueError:
        return False
    return True if np.abs(num) <= 1 else False


def get_entry_valid_recur(widget):
    return [widget] if isinstance(widget, EntryValid | SpinboxValid) \
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

        # Label(common_params_frame, text='Second gear').grid(row=2, column=0, padx=2, pady=2, sticky=W)
        # self.has_gear1 = IntVar()
        # self.gear1_cb = Checkbutton(common_params_frame, variable=self.has_gear1, selectcolor='lemon chiffon')
        # self.gear1_cb.grid(row=2, column=1, padx=2, pady=2, sticky=E)
        # self.has_gear1.trace('w', self.checkbtn_callback)

        Label(common_params_frame, text='Cutting tool:').grid(row=3, column=0, columnspan=2, padx=10, pady=2, sticky=W)
        self.cutter = IntVar()
        Radiobutton(common_params_frame, text='rack or hob cutter', variable=self.cutter, value=0, selectcolor='lemon chiffon').grid(row=4, column=0, pady=2, sticky=W)

        rb_frame = Frame(common_params_frame)
        rb_frame.grid(row=5, column=0, columnspan=2, pady=2, sticky=W)
        common_params_frame.input_callback = self.input_callback
        Radiobutton(rb_frame, text='gear, ', variable=self.cutter, value=1, selectcolor='lemon chiffon').pack(side=LEFT)
        self.cutter_tooth_num = EntryValid(rb_frame, check_pos_int, width=6, justify='right')
        self.cutter_tooth_num.pack(side=LEFT)
        self.cutter_tooth_num.insert(END, '18')
        Label(rb_frame, text=' teeth').pack(side=LEFT)

        Radiobutton(common_params_frame, text='mating gear', variable=self.cutter, value=2, selectcolor='lemon chiffon').grid(row=6, column=0, pady=2, sticky=W)
        self.cutter.trace('w', self.cutter_callback)

        Label(common_params_frame, text='Profile shift coef').grid(row=7, column=0, padx=2, pady=2, sticky=W)
        # self.profile_shift_coef = EntryValid(common_params_frame, check_float, width=6, justify='right')
        tcl_up_or_down = self.register(self.shift_callback)
        self.step = 0.05
        self.profile_shift_coef = SpinboxValid(common_params_frame, check_abs_one, width=6, from_=-1e10, to=1e10, increment=self.step, command=(tcl_up_or_down, '%d'), justify='right')
        self.profile_shift_coef.grid(row=7, column=1, padx=2, pady=2, sticky=E)
        # self.profile_shift_coef.insert(END, '0')
        self.profile_shift_coef.strvar.set('0')

        # Label(common_params_frame, text='Move rack:').grid(row=8, column=0, columnspan=2, padx=10, pady=2, sticky=W)
        # btn_frame = Frame(common_params_frame)
        # btn_frame.grid(row=9, column=0, columnspan=2, padx=10, pady=0, sticky=W)
        # step = 0.05
        # Button(btn_frame, text=f'+{step}', width=2, command=lambda: self.shift_callback(step)).pack(padx=2, pady=2, side=LEFT)
        # Button(btn_frame, text=f'-{step}', width=2, command=lambda: self.shift_callback(-step)).pack(padx=2, pady=2, side=LEFT)



            # Gear 1
        params0_frame = LabelFrame(self, labelwidget=Label(self, text='Gear A', font=('Times', 10, 'italic')),
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
        params1_frame = LabelFrame(self, labelwidget=Label(self, text='Gear B', font=('Times', 10, 'italic')),
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
        # self.gear1_inputs = get_entry_valid_recur(params1_frame)
        # self.checkbtn_callback()
        self.cutter_callback()

    # Input callbacks
    def input_callback(self):
        if self.input_fields:
            if all([field.is_valid for field in self.input_fields]):
                self.master.master.toolbar.activate()
            else:
                self.master.master.toolbar.deactivate()

    # def checkbtn_callback(self, *args):
    #     state = NORMAL if self.has_gear1.get() else DISABLED
    #     for input_field in self.gear1_inputs:
    #         input_field.config(state=state)

    def cutter_callback(self, *args):
        self.cutter_tooth_num.config(state=(NORMAL if self.cutter.get() == 1 else DISABLED))

    # def shift_callback(self, term, *args):
    #     affected_vars = ((self.profile_shift_coef, 1), (self.ad_coef0, 1), (self.de_coef0, -1), (self.ad_coef1, -1), (self.de_coef1, 1))
    #     for affected_var, sign in affected_vars:
    #         try:
    #             old_val = float(affected_var.strvar.get())
    #         except ValueError:
    #             continue
    #         affected_var.delete(0, END)
    #         affected_var.insert(END, str(round(old_val + term * sign, 5)))

    def shift_callback(self, direction):
        self.profile_shift_coef.entry_callback()
        dir_ = 1 if direction == 'up' else -1
        affected_vars = ((self.ad_coef0, 1), (self.de_coef0, -1), (self.ad_coef1, -1), (self.de_coef1, 1))
        for affected_var, sign in affected_vars:
            try:
                old_val = float(affected_var.strvar.get())
            except ValueError:
                continue
            affected_var.delete(0, END)
            affected_var.insert(END, str(round(old_val + self.step * sign * dir_, 5)))

    # Value getters
    @property
    def module_val(self):
        return float(self.module.strvar.get())

    @property
    def pressure_angle_val(self):
        return np.deg2rad(float(self.pressure_angle.strvar.get()))

    @property
    def tooth_num0_val(self):
        return int(self.tooth_num0.strvar.get())

    @property
    def ad_coef0_val(self):
        return float(self.ad_coef0.strvar.get())

    @property
    def de_coef0_val(self):
        return float(self.de_coef0.strvar.get())

    @property
    def tooth_num1_val(self):
        return int(self.tooth_num1.strvar.get())

    @property
    def ad_coef1_val(self):
        return float(self.ad_coef1.strvar.get())

    @property
    def de_coef1_val(self):
        return float(self.de_coef1.strvar.get())

    @property
    def cutter_teeth_num0(self):
        return self.cutter_teeth_num_val(0)

    @property
    def cutter_teeth_num1(self):
        return self.cutter_teeth_num_val(1)

    @property
    def profile_shift_coef_val(self):
        return float(self.profile_shift_coef.strvar.get())

    def cutter_teeth_num_val(self, gear_idx):
        cutter_val = self.cutter.get()
        if cutter_val == 0:
            return 0
        elif cutter_val == 1:
            return int(self.cutter_tooth_num.get())
        else:
            return (self.tooth_num1_val, self.tooth_num0_val)[gear_idx]


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

        notebook = ttk.Notebook(main_frame, width=10000, height=10000)
        notebook.pack(padx=2, pady=2, side=RIGHT)
        # ttk.Style().configure("TNotebook", background='red')


            # Plots frame
        self.plots_frame = Frame(notebook)
        self.plots_frame.pack(side=LEFT, fill=BOTH, expand=True)
        notebook.add(self.plots_frame, text='Simulation')
        # self.globplot_frame = LabelFrame(plots_frame, labelwidget=Label(plots_frame, text='Simulation',
        #                                  font=('Times', 10, 'italic')), labelanchor=N)
        # self.globplot_frame.pack(padx=2, pady=2, ipady=0, fill=BOTH, expand=True)

            # Text frame
        self.text_frame = Frame(notebook)
        self.text_frame.pack(side=LEFT, fill=BOTH, expand=True)
        notebook.add(self.text_frame, text='Data')

        msg_subframe = Frame(self.text_frame)
        msg_subframe.pack(padx=4, pady=3, fill=BOTH, expand=True)

        txt_btn_frame = Frame(msg_subframe)
        txt_btn_frame.pack(side=BOTTOM, fill=X, pady=1)
        Button(txt_btn_frame, text='Save', width=6, command=self.save_text).pack(side=RIGHT)

        self.txt = Text(msg_subframe, height=10, width=20, state='disabled')
        self.txt.config(tabs=tkfont.Font(font=self.txt['font']).measure('    '))
        yscrollbar = ttk.Scrollbar(msg_subframe, command=self.txt.yview)
        yscrollbar.pack(side=RIGHT, pady=2, fill=Y)
        self.txt.pack(side=RIGHT, pady=1, fill=BOTH, expand=True)
        self.txt.config(yscrollcommand=yscrollbar.set)
        # self.text_msg('App started\n'*100)
        # print(dir(notebook))

            # Matplotlib canvas
        self.fig = Figure(figsize=(10, 8))
        self.fig.set_tight_layout(True)
        self.fig.set_facecolor(self.cget("background"))
        self.ax = self.fig.add_subplot()
        self.ax.set_aspect('equal', 'box')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plots_frame)
        self.ax.plot([], [], color='b', linewidth=1)
        self.ax.plot([], [], color='r', linewidth=1)
        self.ax.set_xlim((0, 1))
        self.ax.set_ylim((0, 1))
        self.toolbar = ToolbarPlayer(self.canvas, self.plots_frame, self.play, self.next_frame, self.pause,
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

        self.tooth0 = HalfTooth(tooth_num=self.inputs.tooth_num0_val,
                                module=self.inputs.module_val,
                                pressure_angle=self.inputs.pressure_angle_val,
                                ad_coef=self.inputs.ad_coef0_val,
                                de_coef=self.inputs.de_coef0_val,
                                cutter_teeth_num=self.inputs.cutter_teeth_num0)
        self.tooth1 = HalfTooth(tooth_num=self.inputs.tooth_num1_val,
                                module=self.inputs.module_val,
                                pressure_angle=self.inputs.pressure_angle_val,
                                ad_coef=self.inputs.ad_coef1_val,
                                de_coef=self.inputs.de_coef1_val,
                                cutter_teeth_num=self.inputs.cutter_teeth_num1)

        xy_lims = (float('inf'), float('inf'), float('-inf'), float('-inf'))

        if self.has_gear0:
            self.gear_sector0 = GearSector(self.tooth0, self.tooth0, step_cnt=100, sector=(np.pi*1.5, np.pi*0.5),
                                           rot_ang=0, is_acw=False)
            self.rotating_gear_sector0 = iter(self.gear_sector0)
            ctr_circ = Circle((0, 0), self.gear_sector0.ht0.pitch_radius * 0.01, color='b')
            self.ax.add_patch(ctr_circ)
            xy_lims = merge_xy_lims(*xy_lims, *self.gear_sector0.get_limits())
            xy_lims = upd_xy_lims(0, 0, *xy_lims)

        if self.has_gear1:
            self.gear_sector1 = GearSector(self.tooth1, self.tooth1, step_cnt=100, sector=(np.pi*0.5, np.pi*1.5),
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

        self.text_msg(
            'Gear A parameters\n\n'
            f'{indentate(str(self.tooth0))}'
            '\n\n\nGear B parameters\n\n'
            f'{indentate(str(self.tooth1))}'
        )
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

    def text_msg(self, msg):
        self.txt.configure(state='normal')
        self.txt.delete(1.0, END)
        self.txt.insert(END, msg)
        self.txt.configure(state='disabled')
        self.txt.yview_moveto(1.0)

    def save_text(self):
        filepath = filedialog.asksaveasfilename(filetypes=[('txt file', '.txt')], defaultextension='.txt', initialfile='params.txt')
        with open(filepath, 'w') as output_file:
            output_file.write(self.txt.get("1.0", "end-1c"))


if __name__ == '__main__':
    gears_app = GearsApp()
    gears_app.mainloop()
    