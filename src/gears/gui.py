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

from .helpers import bool_to_sign
from .helpers import Clock
from .helpers import indentate
from .helpers import merge_xy_lims
from .helpers import upd_xy_lims
from .tooth_profile import GearSector
from .tooth_profile import HalfTooth
from .tooth_profile import Rack
from .tooth_profile import Transmission


class State(Enum):
    PAUSE: int = auto()
    RESUME: int = auto()
    RESET: int = auto()
    PLAY: int = auto()


class ToolbarPlayer(NavigationToolbar2Tk):
    """Child class with extra buttons to support animation."""

    def __init__(self, canvas: FigureCanvasTkAgg, window: Widget, callback_play: Callable[[], None],
                 callback_next_frame: Callable[[], None], callback_pause: Callable[[], None],
                 callback_resume: Callable[[], None], callback_stop: Callable[[], None]) -> None:
        self.canvas = canvas
        self.callback_play = callback_play
        self.callback_pause = callback_pause
        self.callback_resume = callback_resume
        self.clock = Clock()

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

    def set_btn_img(self, btn: Button, img: str) -> None:
        btn._image_file = img  # type: ignore[attr-defined]
        ToolbarPlayer._set_image_for_button(self, btn)

    def pause_state(self) -> None:
        self.play_btn.config(command=self.callback_resume)
        self.set_btn_img(self.play_btn, self.play_img)
        self.next_btn.config(state=NORMAL)
        self.state = State.PAUSE

    def resume_state(self) -> None:
        self.next_btn.config(state=DISABLED)
        self.play_btn.config(command=self.callback_pause)
        self.set_btn_img(self.play_btn, self.pause_img)
        self.state = State.RESUME

    def reset_state(self) -> None:
        self.play_btn.config(command=self.callback_play)
        self.set_btn_img(self.play_btn, self.play_img)
        self.stop_btn.config(state=DISABLED)
        self.next_btn.config(state=DISABLED)
        self.cnt_lbl['text'] = ''
        self.state = State.RESET

    def play_state(self) -> None:
        self.stop_btn.config(state=NORMAL)
        self.play_btn.config(command=self.callback_pause)
        self.set_btn_img(self.play_btn, self.pause_img)
        self.state = State.PLAY

    def upd_frame_num(self) -> None:
        self.cnt_lbl['text'] = f'#{self.clock.i}'

    def activate(self) -> None:
        if self.state == State.RESET:
            self.play_btn.config(state=NORMAL)

    def deactivate(self) -> None:
        if self.state == State.RESET:
            self.play_btn.config(state=DISABLED)

    def save_figure(self, *args):
        self.canvas.figure.set_facecolor('#ffffff00')
        super().save_figure(*args)
        self.canvas.figure.set_facecolor(self.cget("background"))


class InputWidgetValidatorMixin():
    """Mixin: validation support for input widgets."""

    def __init__(self, parent: Widget, input_callback: Callable[[], None], validator: Callable[[str], bool], **kwargs):
        self.input_callback = input_callback
        self.validator = validator
        self.strvar = StringVar(parent)
        self.strvar.trace('w', self.entry_callback)
        kwargs['textvariable'] = self.strvar
        super().__init__(parent, **kwargs)  # type: ignore[call-arg]
        self.entry_callback()

    def entry_callback(self, *args):
        self.is_valid = self.validator(self.strvar.get()) or self['state'] == DISABLED
        self['bg'] = 'lemon chiffon' if self.is_valid else '#fca7b8'
        self.input_callback()


class EntryValid(InputWidgetValidatorMixin, Entry):
    """Entry widget with validation. Validator func must be added as the 2nd argument."""


class SpinboxValid(InputWidgetValidatorMixin, Spinbox):
    """Spinbox widget with validation. Validator func must be added as the 2nd argument."""


# User input validators
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
    """Input frame. The component of gear app main window."""

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
        self.module = EntryValid(common_params_frame, self.input_callback, check_pos_finite, width=6, justify='right')
        self.module.grid(row=0, column=1, padx=2, pady=2, sticky=E)
        self.module.insert(END, '10')

        Label(common_params_frame, text='Pressure angle').grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.pressure_angle = EntryValid(common_params_frame, self.input_callback, check_90_deg, width=6,
                                         justify='right')
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
        self.cutter_tooth_num = EntryValid(rb_frame, self.input_callback, check_pos_int, width=6, justify='right')
        self.cutter_tooth_num.pack(side=LEFT)
        self.cutter_tooth_num.insert(END, '18')
        Label(rb_frame, text=' teeth').pack(side=LEFT)

        Radiobutton(common_params_frame, text='mating gear', variable=self.cutter, value=2,
                    selectcolor='lemon chiffon').grid(row=6, column=0, pady=2, sticky=W)
        self.cutter.trace('w', self.cutter_callback)

        Label(common_params_frame, text='Profile shift coef').grid(row=7, column=0, padx=2, pady=2, sticky=W)
        tcl_up_or_down = self.register(self.shift_callback)
        self.step = 0.02
        self.profile_shift_coef = SpinboxValid(common_params_frame, self.input_callback, check_abs_one, width=6,
                                               from_=-1e10, to=1e10, increment=self.step,
                                               command=(tcl_up_or_down, '%d'), justify='right')
        self.profile_shift_coef.grid(row=7, column=1, padx=2, pady=2, sticky=E)
        self.profile_shift_coef.strvar.set('0')

        # Gear 1
        params0_frame = LabelFrame(self, labelwidget=Label(self, text='Gear A', font=('Times', 10, 'italic')),
                                   labelanchor=N)
        params0_frame.pack(side=TOP, padx=2, pady=2, fill=X)
        params0_frame.columnconfigure(0, weight=1)

        Label(params0_frame, text='Number of teeth').grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.tooth_num0 = EntryValid(params0_frame, self.input_callback, check_pos_int, width=6, justify='right')
        self.tooth_num0.grid(row=0, column=1, padx=2, pady=2, sticky=E)
        self.tooth_num0.insert(END, '40')

        Label(params0_frame, text='Addendum coef').grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.ad_coef0 = EntryValid(params0_frame, self.input_callback, check_pos_finite, width=6, justify='right')
        self.ad_coef0.grid(row=1, column=1, padx=2, pady=2, sticky=E)
        self.ad_coef0.insert(END, '1')

        Label(params0_frame, text='Dedendum coef').grid(row=2, column=0, padx=2, pady=2, sticky=W)
        self.de_coef0 = EntryValid(params0_frame, self.input_callback, check_pos_finite, width=6, justify='right')
        self.de_coef0.grid(row=2, column=1, padx=2, pady=2, sticky=E)
        self.de_coef0.insert(END, '1')

        # Gear 2
        params1_frame = LabelFrame(self, labelwidget=Label(self, text='Gear B', font=('Times', 10, 'italic')),
                                   labelanchor=N)
        params1_frame.pack(side=TOP, padx=2, pady=2, fill=X)
        params1_frame.columnconfigure(0, weight=1)

        Label(params1_frame, text='Number of teeth').grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.tooth_num1 = EntryValid(params1_frame, self.input_callback, check_pos_int, width=6, justify='right')
        self.tooth_num1.grid(row=0, column=1, padx=2, pady=2, sticky=E)
        self.tooth_num1.insert(END, '40')

        Label(params1_frame, text='Addendum coef').grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.ad_coef1 = EntryValid(params1_frame, self.input_callback, check_pos_finite, width=6, justify='right')
        self.ad_coef1.grid(row=1, column=1, padx=2, pady=2, sticky=E)
        self.ad_coef1.insert(END, '1')

        Label(params1_frame, text='Dedendum coef').grid(row=2, column=0, padx=2, pady=2, sticky=W)
        self.de_coef1 = EntryValid(params1_frame, self.input_callback, check_pos_finite, width=6, justify='right')
        self.de_coef1.grid(row=2, column=1, padx=2, pady=2, sticky=E)
        self.de_coef1.insert(END, '1')

        self.input_fields = get_entry_valid_recur(self)

    # Input callbacks
    def input_callback(self) -> None:
        if self.input_fields:
            if all([field.is_valid for field in self.input_fields]):
                self.master.master.toolbar.activate()  # type: ignore[union-attr]
            else:
                self.master.master.toolbar.deactivate()  # type: ignore[union-attr]

    def cutter_callback(self, *args) -> None:
        self.cutter_tooth_num.config(state=(NORMAL if self.cutter.get() == 1 else DISABLED))
        self.cutter_tooth_num.entry_callback()
        self.input_callback()

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
    def pressure_angle_rad_val(self) -> float:
        return np.deg2rad(float(self.pressure_angle.strvar.get()))

    @property
    def tooth_num_vals(self) -> tuple[int, int]:
        return int(self.tooth_num0.strvar.get()), int(self.tooth_num1.strvar.get())

    @property
    def ad_coef_vals(self) -> tuple[float, float]:
        return float(self.ad_coef0.strvar.get()), float(self.ad_coef1.strvar.get())

    @property
    def de_coef_vals(self) -> tuple[float, float]:
        return float(self.de_coef0.strvar.get()), float(self.de_coef1.strvar.get())

    @property
    def cutter_teeth_nums(self) -> tuple[int, int]:
        cutter_val = self.cutter.get()
        if cutter_val == 0:
            return 0, 0
        elif cutter_val == 1:
            return (int(self.cutter_tooth_num.get()),) * 2
        else:
            return self.tooth_num_vals[::-1]

    @property
    def profile_shift_coef_val(self) -> float:
        return float(self.profile_shift_coef.strvar.get())


class MenuBar(Menu):
    def __init__(self, parent: Tk, callback_gear: Callable[[int], None], callback_action_lines: Callable[[], None],
                 callback_contact_points: Callable[[], None], callback_rack: Callable[[], None]):
        super().__init__(parent, relief=FLAT, bg='gray88')

        viewmenu = Menu(self, tearoff=0)

        # Declare variables
        self.has_gears = (BooleanVar(self, True), BooleanVar(self, True))
        self.has_action_line = BooleanVar(self, False)
        self.has_contact_pts = BooleanVar(self, False)
        self.has_rack = BooleanVar(self, False)

        # Add buttons
        viewmenu.add_checkbutton(label='Gear A', onvalue=True, offvalue=False, variable=self.has_gears[0],
                                 command=lambda: callback_gear(0))
        viewmenu.add_checkbutton(label='Gear B', onvalue=True, offvalue=False, variable=self.has_gears[1],
                                 command=lambda: callback_gear(1))
        viewmenu.add_checkbutton(label='Action line', onvalue=True, offvalue=False, variable=self.has_action_line,
                                 command=callback_action_lines)
        viewmenu.add_checkbutton(label='Contact points', onvalue=True, offvalue=False, variable=self.has_contact_pts,
                                 command=callback_contact_points)
        viewmenu.add_checkbutton(label='Rack', onvalue=True, offvalue=False, variable=self.has_rack,
                                 command=callback_rack)

        # Mount
        self.add_cascade(label='View', menu=viewmenu)
        parent.config(menu=self)


class GearsApp(Tk):
    """Gears app with GUI"""

    teeth: list[HalfTooth]
    gear_sectors: list[GearSector]
    transmission: Transmission
    rack: Rack

    def __init__(self) -> None:
        super().__init__()

        # Window setup
        self.title('GEARS')
        self.geometry('1000x800')
        self.resizable(True, True)

        # Menu bar
        self.menubar = MenuBar(self, callback_gear=self.show_gear, callback_action_lines=self.show_action_lines,
                               callback_contact_points=self.show_contact_points, callback_rack=self.show_rack)

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
        notebook.add(self.plots_frame, text='Animation')

        # Text frame
        self.text_frame = Frame(notebook)
        self.text_frame.pack(side=LEFT, fill=BOTH, expand=True)
        notebook.add(self.text_frame, text='Data')

        msg_subframe = Frame(self.text_frame)
        msg_subframe.pack(padx=4, pady=3, fill=BOTH, expand=True)

        txt_btn_frame = Frame(msg_subframe)
        txt_btn_frame.pack(side=BOTTOM, fill=X, pady=1)
        Button(txt_btn_frame, text='Save', width=6, command=self.save_text).pack(side=RIGHT)

        self.txt = Text(msg_subframe, height=10, width=20, state=DISABLED)
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
        self.ax.plot([], [], color='grey', linewidth=1)  # type: ignore[call-arg]
        self.ax.plot([], [], color='grey', linewidth=1)  # type: ignore[call-arg]
        self.ax.plot([], [], marker='o', markersize=5, mec='g', mfc=(1, 1, 1, 0),
                     linestyle='None')  # type: ignore[call-arg, arg-type]
        self.ax.plot([], [], marker='o', markersize=5, mec='m', mfc=(1, 1, 1, 0),
                     linestyle='None')  # type: ignore[call-arg, arg-type]
        self.ax.plot([], [], color='brown', linewidth=1)  # type: ignore[call-arg]
        self.ax.set_xlim((0, 1))  # type: ignore[arg-type]
        self.ax.set_ylim((0, 1))  # type: ignore[arg-type]
        self.toolbar = ToolbarPlayer(self.canvas, self.plots_frame, self.play, self.next_frame, self.pause,
                                     self.resume, self.stop)
        self.canvas.get_tk_widget().pack(side=TOP, padx=0, pady=1, fill=BOTH, expand=1)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.gear0data: npt.NDArray = np.array([[], []])
        self.gear1data: npt.NDArray = np.array([[], []])
        self.action_line0data: npt.NDArray = np.array([[], []])
        self.action_line1data: npt.NDArray = np.array([[], []])
        self.contacts0_data: npt.NDArray = np.array([[], []])
        self.contacts1_data: npt.NDArray = np.array([[], []])

        self.inputs.cutter_callback()
        self.delay_ms: int = 1
        self.clock = Clock()
        self.clock.set_step_cnt(100)
        self.active_mode: bool = False
        self.after_id: Optional[str] = None

    # Show or hide elements
    def show_gear(self, idx: int) -> None:
        """
        Show or hide a gear depending on the corresponding checkbox variable.

        Args:
            idx: Gear index.

        Returns:
            None.
        """
        if self.active_mode:
            flag = self.menubar.has_gears[idx].get()
            self.ax.patches[idx].set_visible(flag)  # type: ignore[attr-defined]
            data = self.gear_sectors[idx].get_data()
            data[0] += bool_to_sign(idx) * self.teeth[idx].pitch_radius
            self.plot_data(self.ax.lines[idx],  # type: ignore[attr-defined]
                           *(data if flag else np.array([[], []])))

    def show_action_lines(self) -> None:
        """
        Show or hide the action line depending on the corresponding checkbox variable.

        Returns:
            None.
        """
        flag = self.menubar.has_action_line.get() and self.active_mode and hasattr(self, 'transmission')
        self.plot_data(self.ax.lines[2],  # type: ignore[attr-defined]
                       *(self.transmission.action_line0data if flag else np.array([[], []])))
        self.plot_data(self.ax.lines[3],  # type: ignore[attr-defined]
                       *(self.transmission.action_line1data if flag else np.array([[], []])))

    def show_contact_points(self) -> None:
        """
        Show or hide the contact points depending on the corresponding checkbox variable.

        Returns:
            None.
        """
        flag = self.menubar.has_contact_pts.get() and self.active_mode and hasattr(self, 'transmission')
        self.plot_data(self.ax.lines[4],  # type: ignore[attr-defined]
                       *(self.transmission.get_data()[0] if flag else np.array([[], []])))
        self.plot_data(self.ax.lines[5],  # type: ignore[attr-defined]
                       *(self.transmission.get_data()[1] if flag else np.array([[], []])))

    def show_rack(self) -> None:
        """
        Show or hide the rack depending on the corresponding checkbox variable.

        Returns:
            None.
        """
        flag = self.menubar.has_rack.get() and self.active_mode
        self.plot_data(self.ax.lines[6],  # type: ignore[attr-defined]
                       *(self.rack.get_data() if flag else np.array([[], []])))

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
        xy_lims = (float('inf'), float('inf'), float('-inf'), float('-inf'))

        # Gears setup
        self.teeth, self.gear_sectors = [], []
        for i, (is_acw, sector, rot_ang, color, x_sign) in enumerate([
            (False, (np.pi * 1.5, np.pi * 0.5), 0, 'b', -1),
            (True, (np.pi * 0.5, np.pi * 1.5), np.pi, 'r', 1)
        ]):
            tooth = HalfTooth(tooth_num=self.inputs.tooth_num_vals[i],
                              module=self.inputs.module_val,
                              pressure_angle_rad=self.inputs.pressure_angle_rad_val,
                              ad_coef=self.inputs.ad_coef_vals[i],
                              de_coef=self.inputs.de_coef_vals[i],
                              profile_shift_coef=self.inputs.profile_shift_coef_val * x_sign,
                              cutter_teeth_num=self.inputs.cutter_teeth_nums[i],
                              resolution=self.inputs.module_val * 0.01)
            gear_sector = GearSector(tooth, tooth, sector=sector, rot_ang=rot_ang, is_acw=is_acw)
            ctr_x = tooth.pitch_radius * x_sign
            ctr_circ = Circle((ctr_x, 0), gear_sector.ht0.pitch_radius * 0.01, color=color)
            self.ax.add_patch(ctr_circ)  # type: ignore[attr-defined]
            xy_lims_ = gear_sector.get_limits()
            xy_lims = merge_xy_lims(*xy_lims, xy_lims_[0] + ctr_x, xy_lims_[1], xy_lims_[2] + ctr_x, xy_lims_[3])
            self.teeth.append(tooth)
            self.gear_sectors.append(gear_sector)
        xy_lims = upd_xy_lims(-self.teeth[0].pitch_radius, self.teeth[1].pitch_radius, *xy_lims)

        # Action lines and contact points setup
        self.transmission = Transmission(*self.teeth)

        # Rack setup
        self.rack = Rack(module=self.inputs.module_val,
                         pressure_angle_rad=self.inputs.pressure_angle_rad_val,
                         ad_coef=self.teeth[1].de_coef,
                         de_coef=self.teeth[0].de_coef,
                         profile_shift_coef=self.inputs.profile_shift_coef_val)
        self.rack.set_smart_boundaries(self.teeth[0], self.teeth[1])
        xy_lims = merge_xy_lims(*xy_lims, *self.rack.get_limits())

        # Set plot limits, add margin
        min_x, min_y, max_x, max_y = xy_lims
        margin = max(max_x - min_x, max_y - min_y) * 0.05
        self.ax.set_xlim((min_x - margin, max_x + margin))  # type: ignore[arg-type]
        self.ax.set_ylim((min_y - margin, max_y + margin))  # type: ignore[arg-type]

        self.active_mode = True
        self.text_msg(
            'Gear A parameters\n\n'
            f'{indentate(str(self.teeth[0]))}'
            '\n\n\nGear B parameters\n\n'
            f'{indentate(str(self.teeth[1]))}'
            '\n\n\nTransmission parameters\n\n'
            f'{indentate(str(self.transmission))}'
        )
        self.show_action_lines()
        self.auto_update_frames()

    def next_frame(self) -> None:
        self.clock.inc()
        for i in range(2):
            self.show_gear(i)
        self.toolbar.upd_frame_num()
        self.show_contact_points()
        self.show_rack()

    def pause(self, event: Optional[KeyEvent] = None) -> None:
        self.break_loop()
        self.toolbar.pause_state()

    def resume(self, event: Optional[KeyEvent] = None) -> None:
        self.toolbar.resume_state()
        self.auto_update_frames()

    def stop(self) -> None:
        """Break loop, reset, and restore the initial appearance"""
        self.break_loop()
        self.active_mode = False
        self.clock.reset()
        [patch.remove() for patch in self.ax.patches]  # type: ignore[attr-defined]
        [self.plot_data(line, [], []) for line in self.ax.lines]  # type: ignore[attr-defined, arg-type, func-returns-value] # noqa: E501
        self.toolbar.reset_state()
        self.inputs.input_callback()

    def save_text(self) -> None:
        """Save the data tab content to a file."""
        filepath = filedialog.asksaveasfilename(
            filetypes=[('txt file', '.txt')], defaultextension='.txt', initialfile='params.txt')
        if filepath in [tuple(), '']:  # No filepath given
            return
        with open(filepath, 'w') as output_file:
            output_file.write(self.txt.get("1.0", "end-1c"))

    # Helpers
    def auto_update_frames(self) -> None:
        self.next_frame()
        self.after_id = self.after(self.delay_ms, self.auto_update_frames)

    def break_loop(self) -> None:
        """Stop circulating frames"""
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None

    def text_msg(self, msg: str) -> None:
        """Print some message in the data tab."""
        self.txt.configure(state=NORMAL)
        self.txt.delete(1.0, END)
        self.txt.insert(END, msg)
        self.txt.configure(state=DISABLED)
