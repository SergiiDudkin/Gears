import os
import tkinter.font as tkfont
import tkinter.ttk as ttk
from enum import auto
from enum import Enum
from tkinter import BooleanVar
from tkinter import BOTH
from tkinter import BOTTOM
from tkinter import Button
from tkinter import DISABLED
from tkinter import E
from tkinter import END
from tkinter import Entry
from tkinter import filedialog
from tkinter import FLAT
from tkinter import Frame
from tkinter import IntVar
from tkinter import Label
from tkinter import LabelFrame
from tkinter import LEFT
from tkinter import Menu
from tkinter import N
from tkinter import NORMAL
from tkinter import Radiobutton
from tkinter import RIGHT
from tkinter import Spinbox
from tkinter import StringVar
from tkinter import Text
from tkinter import Tk
from tkinter import TOP
from tkinter import W
from tkinter import Widget
from tkinter import X
from tkinter import Y
from typing import Callable
from typing import cast
from typing import Optional

import numpy as np
import numpy.typing as npt
from matplotlib.backend_bases import key_press_handler  # type: ignore[attr-defined]
from matplotlib.backend_bases import KeyEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.pyplot import Circle  # type: ignore[attr-defined]

from .helpers import indentate
from .tooth_profile import GearSector
from .tooth_profile import get_action_line
from .tooth_profile import HalfTooth
from .transforms import merge_xy_lims
from .transforms import upd_xy_lims


class State(Enum):
    PAUSE: int = auto()
    RESUME: int = auto()
    RESET: int = auto()
    PLAY: int = auto()


class ToolbarPlayer(NavigationToolbar2Tk):
    def __init__(self, canvas: FigureCanvasTkAgg, window: Widget, callback_play: Callable[[], None],
                 callback_next_frame: Callable[[], None], callback_pause: Callable[[], None],
                 callback_resume: Callable[[], None], callback_stop: Callable[[], None]) -> None:
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

    def __init__(self, parent: Widget, validator, **kwargs):
        self.input_callback = cast(InputFrame, parent.master).input_callback
        self.validator = validator
        self.strvar = StringVar(parent)
        self.strvar.trace('w', self.entry_callback)
        kwargs['textvariable'] = self.strvar
        super().__init__(parent, **kwargs)
        self.entry_callback()

    def entry_callback(self, *args) -> None:
        self.is_valid = self.validator(self.strvar.get())
        self['bg'] = 'lemon chiffon' if self.is_valid else '#fca7b8'
        self.input_callback()


def check_pos_int(strvar: str) -> bool:
    try:
        num = int(strvar)
    except ValueError:
        return False
    return True if num > 0 else False


def check_pos_finite(strvar: str) -> bool:
    try:
        num = float(strvar)
    except ValueError:
        return False
    return True if (num > 0 and num != float('inf')) else False


def check_90_deg(strvar: str) -> bool:
    try:
        num = float(strvar)
    except ValueError:
        return False
    return True if (0 < num < 90) else False


def check_float(strvar: str) -> bool:
    try:
        float(strvar)
        return True
    except ValueError:
        return False


def check_abs_one(strvar: str) -> bool:
    try:
        num = float(strvar)
    except ValueError:
        return False
    return True if np.abs(num) <= 1 else False


def get_entry_valid_recur(widget: Widget) -> list[EntryValid | SpinboxValid]:
    return [widget] if isinstance(widget, EntryValid | SpinboxValid) \
        else [item for child in widget.winfo_children() for item in get_entry_valid_recur(child)]


class InputFrame(Frame):
    def __init__(self, parent: Widget) -> None:
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

        Label(common_params_frame, text='Cutting tool:').grid(row=3, column=0, columnspan=2, padx=10, pady=2, sticky=W)
        self.cutter = IntVar()
        Radiobutton(common_params_frame, text='rack or hob cutter', variable=self.cutter,
                    value=0, selectcolor='lemon chiffon').grid(row=4, column=0, pady=2, sticky=W)

        rb_frame = Frame(common_params_frame)
        rb_frame.grid(row=5, column=0, columnspan=2, pady=2, sticky=W)
        common_params_frame.input_callback = self.input_callback  # type: ignore[attr-defined]
        Radiobutton(rb_frame, text='gear, ', variable=self.cutter, value=1, selectcolor='lemon chiffon').pack(side=LEFT)
        self.cutter_tooth_num = EntryValid(rb_frame, check_pos_int, width=6, justify='right')
        self.cutter_tooth_num.pack(side=LEFT)
        self.cutter_tooth_num.insert(END, '18')
        Label(rb_frame, text=' teeth').pack(side=LEFT)

        Radiobutton(common_params_frame, text='mating gear', variable=self.cutter, value=2,
                    selectcolor='lemon chiffon').grid(row=6, column=0, pady=2, sticky=W)
        self.cutter.trace('w', self.cutter_callback)

        Label(common_params_frame, text='Profile shift coef').grid(row=7, column=0, padx=2, pady=2, sticky=W)
        tcl_up_or_down = self.register(self.shift_callback)
        self.step = 0.05
        self.profile_shift_coef = SpinboxValid(common_params_frame, check_abs_one, width=6, from_=-1e10, to=1e10,
                                               increment=self.step, command=(tcl_up_or_down, '%d'), justify='right')
        self.profile_shift_coef.grid(row=7, column=1, padx=2, pady=2, sticky=E)
        self.profile_shift_coef.strvar.set('0')

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
        self.cutter_callback()

    # Input callbacks
    def input_callback(self) -> None:
        if self.input_fields:
            if all([field.is_valid for field in self.input_fields]):
                self.master.master.toolbar.activate()  # type: ignore[union-attr]
            else:
                self.master.master.toolbar.deactivate()  # type: ignore[union-attr]

    def cutter_callback(self, *args) -> None:
        self.cutter_tooth_num.config(state=(NORMAL if self.cutter.get() == 1 else DISABLED))

    def shift_callback(self, direction: str) -> None:
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
    def module_val(self) -> float:
        return float(self.module.strvar.get())

    @property
    def pressure_angle_val(self) -> float:
        return np.deg2rad(float(self.pressure_angle.strvar.get()))

    @property
    def tooth_num0_val(self) -> int:
        return int(self.tooth_num0.strvar.get())

    @property
    def ad_coef0_val(self) -> float:
        return float(self.ad_coef0.strvar.get())

    @property
    def de_coef0_val(self) -> float:
        return float(self.de_coef0.strvar.get())

    @property
    def tooth_num1_val(self) -> int:
        return int(self.tooth_num1.strvar.get())

    @property
    def ad_coef1_val(self) -> float:
        return float(self.ad_coef1.strvar.get())

    @property
    def de_coef1_val(self) -> float:
        return float(self.de_coef1.strvar.get())

    @property
    def cutter_teeth_num0(self) -> int:
        return self.cutter_teeth_num_val(0)

    @property
    def cutter_teeth_num1(self) -> int:
        return self.cutter_teeth_num_val(1)

    @property
    def profile_shift_coef_val(self) -> float:
        return float(self.profile_shift_coef.strvar.get())

    def cutter_teeth_num_val(self, gear_idx: int) -> int:
        cutter_val = self.cutter.get()
        if cutter_val == 0:
            return 0
        elif cutter_val == 1:
            return int(self.cutter_tooth_num.get())
        else:
            return (self.tooth_num1_val, self.tooth_num0_val)[gear_idx]


class GearsApp(Tk):
    """Gears app with GUI"""

    def __init__(self) -> None:
        super().__init__()

        # Window setup
        self.title('GEARS')
        self.geometry('1000x800')
        self.resizable(True, True)

        # Menubar
        menubar = Menu(self, relief=FLAT, bg='gray88')
        viewmenu = Menu(menubar, tearoff=0)
        self.has_gear0 = BooleanVar(self, True)  # Menu checkbutton variable
        self.has_gear1 = BooleanVar(self, True)  # Menu checkbutton variable
        self.has_action_line = BooleanVar(self, False)  # Menu checkbutton variable
        viewmenu.add_checkbutton(label='Gear A', onvalue=True, offvalue=False, variable=self.has_gear0,
                                 command=lambda: self.show_gear(0))
        viewmenu.add_checkbutton(label='Gear B', onvalue=True, offvalue=False, variable=self.has_gear1,
                                 command=lambda: self.show_gear(1))
        viewmenu.add_checkbutton(label='Action line', onvalue=True, offvalue=False, variable=self.has_action_line,
                                 command=self.show_action_lines)
        menubar.add_cascade(label='View', menu=viewmenu)
        self.config(menu=menubar)

        # Frames
        main_frame = Frame(self)
        main_frame.pack(padx=2, pady=2, side=LEFT, fill=BOTH, expand=True)

        # Sidebar
        self.inputs = InputFrame(main_frame)

        notebook = ttk.Notebook(main_frame, width=10000, height=10000)
        notebook.pack(padx=2, pady=2, side=RIGHT)

        # Plots frame
        self.plots_frame = Frame(notebook)
        self.plots_frame.pack(side=LEFT, fill=BOTH, expand=True)
        notebook.add(self.plots_frame, text='Simulation')

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

        # Matplotlib canvas
        self.fig = Figure(figsize=(10, 8))
        self.fig.set_tight_layout(True)  # type: ignore[attr-defined]
        self.fig.set_facecolor(self.cget("background"))
        self.ax = self.fig.add_subplot()
        self.ax.set_aspect('equal', 'box')  # type: ignore[attr-defined]
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plots_frame)
        self.ax.plot([], [], color='b', linewidth=1)  # type: ignore[call-arg]
        self.ax.plot([], [], color='r', linewidth=1)  # type: ignore[call-arg]
        self.ax.plot([], [], color='k', linewidth=1)  # type: ignore[call-arg]
        self.ax.plot([], [], color='k', linewidth=1)  # type: ignore[call-arg]
        self.ax.set_xlim((0, 1))  # type: ignore[arg-type]
        self.ax.set_ylim((0, 1))  # type: ignore[arg-type]
        self.toolbar = ToolbarPlayer(self.canvas, self.plots_frame, self.play, self.next_frame, self.pause,
                                     self.resume, self.stop)
        self.canvas.get_tk_widget().pack(side=TOP, padx=0, pady=1, fill=BOTH, expand=1)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.gear0data: npt.NDArray = np.array([[], []])
        self.gear1data: npt.NDArray = np.array([[], []])

        self.inputs.input_callback()
        self.delay_ms = 1
        self.after_id: Optional[str] = None

    def show_gear(self, idx: int) -> None:
        """
        Show or hide a gear depending on the corresponding checkbox variable.

        Args:
            idx: Gear index.

        Returns:
            None.
        """
        flag = getattr(self, f'has_gear{idx}').get()
        self.ax.patches[idx].set_visible(flag)  # type: ignore[attr-defined]
        self.plot_data(self.ax.lines[idx],  # type: ignore[attr-defined]
                       *(getattr(self, f'gear{idx}data') if flag else np.array([[], []])))

    def show_action_lines(self) -> None:
        # res = get_action_line(self.tooth0, self.tooth1)
        # for pt in res:
        #     self.ax.add_patch(Circle((pt[0] + self.tooth0.pitch_radius, pt[1]), 0.5, color='g', fill=False))

        # print(res)
        # circ0 = Circle((res[0] + self.tooth0.pitch_radius, res[1]), self.gear_sector0.ht0.pitch_radius * 0.01,
        #                color='g', fill=False)
        # circ1 = Circle((res[2] + self.tooth0.pitch_radius, res[3]), self.gear_sector0.ht0.pitch_radius * 0.01,
        #                color='g', fill=False)
        # circ2 = Circle((res[4] + self.tooth0.pitch_radius, res[5]), self.gear_sector0.ht0.pitch_radius * 0.01,
        #                color='k', fill=False)
        # circ3 = Circle((res[6] + self.tooth0.pitch_radius, res[7]), self.gear_sector0.ht0.pitch_radius * 0.01,
        #                color='k', fill=False)
        # circ4 = Circle((res[8] + self.tooth0.pitch_radius, res[9]), self.gear_sector0.ht0.pitch_radius * 0.01,
        #                color='c', fill=False)
        # circ5 = Circle((res[10] + self.tooth0.pitch_radius, res[11]), self.gear_sector0.ht0.pitch_radius * 0.01,
        #                color='c', fill=False)
        # circ6 = Circle((res[12] + self.tooth0.pitch_radius, res[13]), self.gear_sector0.ht0.pitch_radius * 0.01,
        #                color='m', fill=False)
        # circ7 = Circle((res[14] + self.tooth0.pitch_radius, res[15]), self.gear_sector0.ht0.pitch_radius * 0.01,
        #                color='m', fill=False)
        # self.ax.add_patch(circ0)  # type: ignore[attr-defined]
        # self.ax.add_patch(circ1)  # type: ignore[attr-defined]
        # self.ax.add_patch(circ2)  # type: ignore[attr-defined]
        # self.ax.add_patch(circ3)  # type: ignore[attr-defined]
        # self.ax.add_patch(circ4)  # type: ignore[attr-defined]
        # self.ax.add_patch(circ5)  # type: ignore[attr-defined]
        # self.ax.add_patch(circ6)  # type: ignore[attr-defined]
        # self.ax.add_patch(circ7)  # type: ignore[attr-defined]

        self.has_action_line.get()
        self.plot_data(self.ax.lines[2],  # type: ignore[attr-defined]
                       *(self.action_line0data if self.has_action_line.get() else np.array([[], []])))

    # Matplotlib funcs

    def on_key_press(self, event: KeyEvent) -> None:
        key_press_handler(event, self.canvas, self.toolbar)

    def plot_data(self, line: Line2D, x_vals: npt.NDArray, y_vals: npt.NDArray) -> None:
        line.set_xdata(np.array(x_vals))
        line.set_ydata(np.array(y_vals))
        self.ax.relim()  # type: ignore[attr-defined] # Recompute the ax.dataLim
        self.ax.autoscale_view()  # type: ignore[attr-defined] # Update ax.viewLim using the new dataLim
        self.canvas.draw()

    # Button callbacks
    def play(self, event: Optional[KeyEvent] = None) -> None:
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

        # pt0, = get_action_line(self.tooth0, self.tooth1)
        self.action_line0data = get_action_line(self.tooth0, self.tooth1)
        self.action_line0data[0] += self.tooth0.pitch_radius

        xy_lims = (float('inf'), float('inf'), float('-inf'), float('-inf'))

        self.gear_sector0 = GearSector(self.tooth0, self.tooth0, step_cnt=100, sector=(np.pi * 1.5, np.pi * 0.5),
                                       rot_ang=0, is_acw=False)
        self.rotating_gear_sector0 = iter(self.gear_sector0)
        ctr_circ = Circle((0, 0), self.gear_sector0.ht0.pitch_radius * 0.01, color='b')
        self.ax.add_patch(ctr_circ)  # type: ignore[attr-defined]
        xy_lims = merge_xy_lims(*xy_lims, *self.gear_sector0.get_limits())
        xy_lims = upd_xy_lims(0, 0, *xy_lims)

        self.gear_sector1 = GearSector(self.tooth1, self.tooth1, step_cnt=100, sector=(np.pi * 0.5, np.pi * 1.5),
                                       rot_ang=np.pi, is_acw=True)
        self.rotating_gear_sector1 = iter(self.gear_sector1)
        self.ctr_dist = self.gear_sector0.ht0.pitch_radius + self.gear_sector1.ht0.pitch_radius
        ctr_circ = Circle((self.ctr_dist, 0), self.gear_sector1.ht0.pitch_radius * 0.01, color='r')
        self.ax.add_patch(ctr_circ)  # type: ignore[attr-defined]
        xy_lims_ = self.gear_sector1.get_limits()
        xy_lims = merge_xy_lims(*xy_lims, xy_lims_[0] + self.ctr_dist, xy_lims_[1], xy_lims_[2] + self.ctr_dist,
                                xy_lims_[3])
        xy_lims = upd_xy_lims(self.ctr_dist, 0, *xy_lims)

        min_x, min_y, max_x, max_y = xy_lims
        margin = max(max_x - min_x, max_y - min_y) * 0.05
        self.ax.set_xlim((min_x - margin, max_x + margin))  # type: ignore[arg-type]
        self.ax.set_ylim((min_y - margin, max_y + margin))  # type: ignore[arg-type]

        self.text_msg(
            'Gear A parameters\n\n'
            f'{indentate(str(self.tooth0))}'
            '\n\n\nGear B parameters\n\n'
            f'{indentate(str(self.tooth1))}'
        )
        self.show_next_frame()

    def next_frame(self) -> None:
        self.show_next_frame()
        self.break_loop()

    def pause(self, event: Optional[KeyEvent] = None) -> None:
        self.break_loop()
        self.toolbar.pause_state()

    def resume(self, event: Optional[KeyEvent] = None) -> None:
        self.toolbar.resume_state()
        self.show_next_frame()

    def stop(self) -> None:
        self.break_loop()
        self.reset()

    # Helpers
    def show_next_frame(self) -> None:
        self.gear0data = next(self.rotating_gear_sector0)
        x_es, y_es = next(self.rotating_gear_sector1)
        self.gear1data = np.vstack((x_es + self.ctr_dist, y_es))
        for i in range(2):
            self.show_gear(i)
        self.toolbar.upd_frame_num(self.gear_sector0.i)
        self.after_id = self.after(self.delay_ms, self.show_next_frame)

    def break_loop(self) -> None:
        """Stop circulating frames"""
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None

    def reset(self) -> None:
        """Restore initial appearance"""
        [patch.remove() for patch in self.ax.patches]  # type: ignore[attr-defined]
        [self.plot_data(line, [], []) for line in self.ax.lines]  # type: ignore[attr-defined, arg-type, func-returns-value] # noqa: E501
        self.toolbar.reset_state()

    def text_msg(self, msg: str) -> None:
        self.txt.configure(state='normal')
        self.txt.delete(1.0, END)
        self.txt.insert(END, msg)
        self.txt.configure(state='disabled')
        self.txt.yview_moveto(1.0)

    def save_text(self) -> None:
        filepath = filedialog.asksaveasfilename(
            filetypes=[('txt file', '.txt')], defaultextension='.txt', initialfile='params.txt')
        with open(filepath, 'w') as output_file:
            output_file.write(self.txt.get("1.0", "end-1c"))


if __name__ == '__main__':
    gears_app = GearsApp()
    gears_app.mainloop()
