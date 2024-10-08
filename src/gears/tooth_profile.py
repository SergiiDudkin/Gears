from typing import Any
from typing import Callable
from typing import cast

import numpy as np
import numpy.typing as npt

from .curves import circle
from .curves import epitrochoid
from .curves import epitrochoid_angrad
from .curves import epitrochoid_flat
from .curves import epitrochoid_flat_angrad
from .curves import involute
from .curves import involute_angrad
from .gear_params import GearParams
from .gear_params import STANDARD_ADDENDUM_COEF
from .gear_params import STANDARD_DEDENDUM_COEF
from .gear_params import STANDARD_PRESSURE_ANGLE
from .geometry import get_unit_vector
from .geometry import is_within_ang
from .geometry import linecirc_intersec
from .geometry import lineline_intersec
from .helpers import bool_to_sign
from .helpers import Clock
from .helpers import sci_round
from .helpers import seedrange
from .helpers import upd_xy_lims
from .transforms import cartesian_to_polar
from .transforms import equidistant
from .transforms import mirror
from .transforms import polar_to_cartesian
from .transforms import rotate

RESOLUTION = 0.1
TOLERANCE = 0.1


class HalfTooth(GearParams):
    """Computation of half tooth profile using given parameters."""

    min_r_cont: float  # Min radius where the involute-involute contact with the cutter takes place

    def __init__(self, tooth_num: int, module: float, pressure_angle_rad: float = STANDARD_PRESSURE_ANGLE,
                 ad_coef: float = STANDARD_ADDENDUM_COEF, de_coef: float = STANDARD_DEDENDUM_COEF,
                 profile_shift_coef: float = 0, cutter_teeth_num: int = 0, resolution: float = RESOLUTION,
                 tolerance: float = TOLERANCE) -> None:
        super().__init__(tooth_num, module, pressure_angle_rad, ad_coef, de_coef)
        self.attrs_to_print += [('is_tooth_undercut', '')]
        self.str_to_replace += [('is tooth undercut', 'tooth undercut')]

        self.cutter_teeth_num = cutter_teeth_num
        self.profile_shift_coef = profile_shift_coef
        self.resolution = resolution
        self.tolerance = tolerance

        self.is_rack = not cutter_teeth_num
        self.my_epitrochoid = cast(Callable, epitrochoid_flat if self.is_rack else epitrochoid)
        self.my_epitrochoid_angrad = epitrochoid_flat_angrad if self.is_rack else epitrochoid_angrad

        self._calc_profile_params()
        self._build_half_tooth()

    def _calc_profile_params(self) -> None:
        self.quater_angle = self.tooth_angle / 4

        if self.is_rack:
            epitrochoid_shift_ang = self._calc_epitrochoid_flat_shift_ang()
        else:
            epitrochoid_shift_ang, cutter_pitch_radius, cutter_outside_radius = self._calc_epitrochoid_shift_ang()
        ang_pitch = involute_angrad(self.pitch_radius, 0, 2, self.base_radius)[0]
        ang_outside, _, _, t_outside = involute_angrad(self.outside_radius, 0, 2, self.base_radius)

        # Consider the profile shift
        profile_ang_shift = self._calc_shift_ang(self.profile_shift_coef * self.module)
        epitrochoid_shift_ang -= profile_ang_shift
        ang_pitch -= profile_ang_shift

        # Gather params of curves
        self.involute_params = {
            'r': self.base_radius,
            'a0': -ang_pitch
        }
        self.epitrochoid_params = {
            'R': self.pitch_radius,
            'l': self.dedendum,
            'a0': -epitrochoid_shift_ang
        } if self.is_rack else {
            'R': self.pitch_radius,
            'r': cutter_pitch_radius,
            'd': cutter_outside_radius,
            'a0': -epitrochoid_shift_ang
        }
        self.outside_circle_params = {
            'r': self.outside_radius,
        }
        self.root_circle_params = {
            'r': self.root_radius,
        }

        invol_epitr_rad, invol_epitr_angle = self._calc_invol_epitr_flat() if self.is_rack else self._calc_invol_epitr()
        self.is_tooth_undercut = invol_epitr_angle * 2 < np.pi
        if self.is_tooth_undercut:
            involute_t_min, epitrochoid_t_max, self.min_r_cont = self._find_involute_epitrochoid_intersection()
        else:
            involute_t_min, epitrochoid_t_max = self._find_involute_epitrochoid_contact_t_vals(invol_epitr_rad)
            self.min_r_cont = invol_epitr_rad

            # Gather limits of curves
        self.involute_lims = (involute_t_min, t_outside)
        self.epitrochoid_lims = (0, epitrochoid_t_max)
        self.outside_circle_lims = (ang_outside - ang_pitch, self.quater_angle)
        self.root_circle_lims = (-self.quater_angle, -epitrochoid_shift_ang)

    def _calc_shift_ang(self, radial_shift: float) -> float:
        proj_onto_rack = radial_shift * np.tan(self.pressure_angle_rad)
        self.shift_percent = proj_onto_rack / self.circular_pitch
        return self.tooth_angle * self.shift_percent  # Shift angle

    def _calc_epitrochoid_flat_shift_ang(self) -> float:
        return self._calc_shift_ang(self.dedendum)

    def _calc_epitrochoid_shift_ang(self) -> tuple[float, float, float]:
        gear_ratio = self.cutter_teeth_num / self.tooth_num
        cutter_base_radius = self.base_radius * gear_ratio
        cutter_pitch_radius = self.pitch_radius * gear_ratio
        cutter_outside_radius = cutter_pitch_radius + self.dedendum
        pitch_ang = involute_angrad(cutter_pitch_radius, 0, 2, cutter_base_radius)[0]
        outside_ang = involute_angrad(cutter_outside_radius, 0, 2, cutter_base_radius)[0]
        epitrochoid_shift_ang = (outside_ang - pitch_ang) * gear_ratio
        return epitrochoid_shift_ang, cutter_pitch_radius, cutter_outside_radius

    def _calc_invol_epitr_flat(self) -> tuple[float, float]:
        """
        Finds the transition point between involute and epitrochoid_flat.

        Returns:
            Radius and angle in polar coordinate system.
        """
        invol_epitr_rad = np.sqrt((self.dedendum / np.tan(self.pressure_angle_rad)) ** 2 + self.root_radius ** 2)
        invol_epitr_angle = np.pi / 2 - np.arccos(self.root_radius / invol_epitr_rad) + self.pressure_angle_rad
        return invol_epitr_rad, invol_epitr_angle

    def _calc_invol_epitr(self) -> tuple[float, float]:
        """
        Finds the transition point between involute and epitrochoid (invalid in case of tooth undercut).

        Returns:
            Radius and angle in polar coordinate system.
        """
        # Solve the first triangle using the law of sines
        b = self.cutter_teeth_num * self.module / 2  # Cutting gear pitch radius
        a = b + self.dedendum
        alpha = np.pi / 2 + self.pressure_angle_rad
        R2t = a / np.sin(alpha)  # Radius of the triangle's circumcircle times 2
        beta = np.arcsin(b / R2t)  # Angle beta is guarantied to be acute
        gamma = np.pi - alpha - beta
        c = R2t * np.sin(gamma)

        # Solve the second triangle using the law of cosines
        c_ = c
        b_ = self.pitch_radius
        alpha_ = np.pi / 2 - self.pressure_angle_rad
        a_ = np.sqrt(b_ ** 2 + c_ ** 2 - 2 * b_ * c_ * np.cos(alpha_))
        beta_ = np.arccos((a_ ** 2 + c_ ** 2 - b_ ** 2) / (2 * a_ * c_))
        invol_epitr_rad, invol_epitr_angle = a_, beta_
        return invol_epitr_rad, invol_epitr_angle

    def _find_involute_epitrochoid_contact_t_vals(self, invol_epitr_rad: float) -> tuple[float, float]:
        """
        Finds values of t param from the given the radius.

        Args:
            invol_epitr_rad: Radial coordinate of involute-epitrochoid contact.

        Returns:
            Limits, i.e. involute t min value, and epitrochoid t max value.
        """
        involute_t_min = involute_angrad(invol_epitr_rad, 0, 1, **self.involute_params)[3]
        epitrochoid_t_max = self.my_epitrochoid_angrad(invol_epitr_rad, 0, -0.1, **self.epitrochoid_params)[3]
        return involute_t_min, epitrochoid_t_max

    def _find_involute_epitrochoid_intersection(self) -> tuple[float, float, float]:
        r_min = self.base_radius
        r_max = self.outside_radius

        for _ in range(100):
            r_curr = np.mean([r_min, r_max])
            involute_ang, _, _, involute_t_min = involute_angrad(r_curr, 0, 1, **self.involute_params)
            epitrochoid_ang, _, _, epitrochoid_t_max = self.my_epitrochoid_angrad(
                r_curr, 0, -0.1, **self.epitrochoid_params)
            if involute_ang == epitrochoid_ang or not (r_min < r_curr < r_max):
                break
            if involute_ang < epitrochoid_ang:
                r_min = r_curr
            else:
                r_max = r_curr
        else:
            print('!!! WARNING! Number of iteration exceeded the limit.')

        return involute_t_min, epitrochoid_t_max, r_curr

    def _build_half_tooth(self) -> None:
        self.points_involute = equidistant(involute, self.involute_lims, self.resolution, self.tolerance,
                                           **self.involute_params)
        self.points_epitrochoid = equidistant(self.my_epitrochoid, self.epitrochoid_lims, self.resolution,
                                              self.tolerance, **self.epitrochoid_params)
        self.points_outside = equidistant(circle, self.outside_circle_lims, self.resolution, self.tolerance,
                                          **self.outside_circle_params)
        self.points_root = equidistant(circle, self.root_circle_lims, self.resolution, self.tolerance,
                                       **self.root_circle_params)

        self.half_tooth_profile = stack_curves(self.points_root, self.points_epitrochoid, self.points_involute,
                                               self.points_outside)

    def get_curves_equations(self) -> dict[str, dict[str, Any]]:
        return {
            'involute': {
                'x': 'r * (cos(t_) + t * sin(t_))',
                'y': 'r * (sin(t_) - t * cos(t_))',
                't_': 't + a0',
                'params': self.involute_params,
                'lims': self.involute_lims
            },
            'epitrochoid': {
                'x': '(R - l) * cos(t_) + t * R * sin(t_)' if self.is_rack else
                '(R + r) * cos(t_) - d * cos(R * t / r + t_)',
                'y': '(R - l) * sin(t_) - t * R * cos(t_)' if self.is_rack else
                '(R + r) * sin(t_) - d * sin(R * t / r + t_)',
                't_': 't + a0',
                'params': self.epitrochoid_params,
                'lims': self.epitrochoid_lims
            },
            'outside circle': {
                'x': 'r * cos(t)',
                'y': 'r * sin(t)',
                'params': self.outside_circle_params,
                'lims': self.outside_circle_lims
            },
            'root circle': {
                'x': 'r * cos(t)',
                'y': 'r * sin(t)',
                'params': self.root_circle_params,
                'lims': self.root_circle_lims
            }
        }

    def __str__(self) -> str:
        output = super().__str__()
        curves_data = self.get_curves_equations()
        for curve_name in ('involute', 'epitrochoid', 'outside circle', 'root circle'):
            curve = curves_data[curve_name]
            curve_str = (
                f'\n\n{curve_name.capitalize()}:'
                f'\n\tx = {curve["x"]}'
                f'\n\ty = {curve["y"]}'
            )
            curve_str += f'\n\tt_ = {curve["t_"]}' if curve.get('t_') else ''
            curve_str += f'\n\tt = {sci_round(curve["lims"][0], 6)} ... {sci_round(curve["lims"][1], 6)}'
            curve_str += '\n\t' + '\n\t'.join(f'{k} = {sci_round(v, 6)}' for k, v in curve['params'].items())
            output += curve_str
        return output


class GearSector:
    """Builds animated gear sector."""

    def __init__(self, halftooth0: HalfTooth, halftooth1: HalfTooth, sector: tuple[float, float] = (0, np.pi),
                 rot_ang: float = 0, is_acw: bool = False) -> None:
        self.ht0 = halftooth0
        self.ht1 = halftooth1
        self.sec_st, self.sec_en = sector
        self.rot_ang = rot_ang
        self.dir = bool_to_sign(is_acw)
        self.clock = Clock()
        self._build_full_tooth()

    def _build_full_tooth(self) -> None:
        sec_st = np.array([0, 0])
        sec_en = np.array([np.cos(-self.ht0.quater_angle), np.sin(-self.ht0.quater_angle)])
        reflected = np.transpose([mirror(point, sec_st, sec_en) for point in np.transpose(self.ht1.half_tooth_profile)])
        self.full_tooth_profile = stack_curves(reflected[:, ::-1], self.ht0.half_tooth_profile)

    def get_gear_profile(self) -> npt.NDArray:
        """Returns the entire gear profile"""
        return populate_circ(*self.full_tooth_profile, self.ht0.tooth_num)  # type: ignore[call-arg]

    def get_sector_profile(self, sec_st: float, sec_en: float, rot_ang: float = 0) -> npt.NDArray:
        st_tooth_idx, full_teeth_ins, en_tooth_idx = self._sortout_teeth(sec_st, sec_en, rot_ang)

        if not full_teeth_ins.size and st_tooth_idx == en_tooth_idx:
            # Case of a single tooth within the sector
            tooth = rotate(*self.full_tooth_profile, self.ht0.tooth_angle *
                           st_tooth_idx + rot_ang)  # type: ignore[call-arg]
            tooth_ang = cartesian_to_polar(*tooth)[0]
            tooth_in_sector_bm = is_within_ang(tooth_ang, sec_st, sec_en)
            pt_ins = np.nonzero(tooth_in_sector_bm)[0]
            try:
                sector_profile = tooth[:, pt_ins[0]: pt_ins[-1] + 1]
            except IndexError:
                raise ValueError('The segment is too narrow; no points inside!')
        else:
            # Case of multiple teeth within the sector
            curves = []

            st_tooth = self._get_term_tooth_profile(st_tooth_idx, sec_st, sec_en, rot_ang, is_en=False)
            curves.append(st_tooth)

            for full_tooth_idx in full_teeth_ins:
                full_tooth = rotate(*self.full_tooth_profile, self.ht0.tooth_angle *
                                    full_tooth_idx + rot_ang)  # type: ignore[call-arg]
                curves.append(full_tooth)

            en_tooth = self._get_term_tooth_profile(en_tooth_idx, sec_st, sec_en, rot_ang, is_en=True)
            curves.append(en_tooth)

            sector_profile = stack_curves(*curves)

        return sector_profile

    def _sortout_teeth(self, sec_st: float, sec_en: float, rot_ang: float = 0) -> tuple[int, npt.NDArray, int]:
        ang0 = cartesian_to_polar(*self.full_tooth_profile[:, 0])[0] + rot_ang
        teeth_sts = np.remainder(ang0 + self.ht0.tooth_angle * np.arange(self.ht0.tooth_num), np.pi * 2)
        teeth_ens = np.roll(teeth_sts, -1)

        teeth_sts_in_sector_bm = is_within_ang(teeth_sts, sec_st, sec_en)
        teeth_sts_in_sector_bm |= teeth_sts == sec_en  # Bug fix for missing tooth
        teeth_ens_in_sector_bm = np.roll(teeth_sts_in_sector_bm, -1)
        seg_st_within_tooth_bm, seg_en_within_tooth_bm = [np.array([is_within_ang(seg_edge, tooth_st, tooth_en)
                                                                    for tooth_st, tooth_en
                                                                    in zip(teeth_sts, teeth_ens)])
                                                          for seg_edge in (sec_st, sec_en)]
        integer_teeth = np.logical_not(seg_st_within_tooth_bm | seg_en_within_tooth_bm)
        full_teeth = teeth_sts_in_sector_bm & teeth_ens_in_sector_bm & integer_teeth

        st_tooth_idx = np.nonzero(seg_st_within_tooth_bm)[0][0]
        full_teeth_ins = np.nonzero(full_teeth)[0]
        if full_teeth_ins.size:
            while (full_teeth_ins[0] - 1) % self.ht0.tooth_num != st_tooth_idx:
                full_teeth_ins = np.roll(full_teeth_ins, 1)
        en_tooth_idx = np.nonzero(seg_en_within_tooth_bm)[0][0]

        return st_tooth_idx, full_teeth_ins, en_tooth_idx

    def _get_term_tooth_profile(self, tooth_idx: int, sec_st: float, sec_en: float, rot_ang: float = 0,
                                is_en: bool = False) -> npt.NDArray:
        tooth = rotate(*self.full_tooth_profile, self.ht0.tooth_angle * tooth_idx + rot_ang)  # type: ignore[call-arg]
        tooth_ang = cartesian_to_polar(*tooth)[0]
        tooth_in_sector_bm = is_within_ang(tooth_ang, sec_st, sec_en)
        try:
            pt_idx = np.nonzero(tooth_in_sector_bm)[0][0 - is_en] + is_en
        except IndexError:
            pt_idx = -1 + is_en
        return tooth[:, :pt_idx] if is_en else tooth[:, pt_idx:]

    def get_data(self) -> npt.NDArray:
        ang_step = self.ht0.tooth_angle / self.clock.step_cnt
        return self.get_sector_profile(self.sec_st, self.sec_en, (ang_step * self.clock.i + self.rot_ang) * self.dir)

    def get_limits(self) -> tuple[float, float, float, float]:
        """
        Get rectangular plot limits.

        Returns:
            min_x, min_y, max_x, max_y
        """
        xy_lims = (float('inf'), float('inf'), float('-inf'), float('-inf'))
        for ang in (self.sec_st, self.sec_en):
            for rad in (self.ht0.root_radius, self.ht0.outside_radius):
                x, y = polar_to_cartesian(ang, rad)
                xy_lims = upd_xy_lims(x, y, *xy_lims)
        for i, (x, y) in enumerate([(1, 0), (0, 1), (-1, 0), (0, -1)]):
            if is_within_ang(i * np.pi / 2, self.sec_st, self.sec_en):
                xy_lims = upd_xy_lims(x * self.ht0.outside_radius, y * self.ht0.outside_radius, *xy_lims)
        return xy_lims


class Transmission:
    """Computes action lines and involute-involute contact points"""

    def __init__(self, tooth0: HalfTooth, tooth1: HalfTooth) -> None:
        self.tooth0 = tooth0
        self.tooth1 = tooth1
        self.action_line0data = self.get_action_line()
        self.action_line1data = np.array([[self.action_line0data[0][1], self.action_line0data[0][0]],
                                          [-self.action_line0data[1][1], -self.action_line0data[1][0]]])
        self.base_step = self.tooth0.base_diameter * np.pi / self.tooth0.tooth_num
        self.ave_contact_points = np.linalg.norm(self.action_line0data[:, 1] -  # type: ignore[attr-defined]
                                                 self.action_line0data[:, 0]) / self.base_step
        self.clock = Clock()

    def get_action_line(self) -> npt.NDArray:
        prv_x, prv_y = rotate(0, 1, self.tooth0.pressure_angle_rad)
        res: list[float] = []
        for tooth, sign in zip([self.tooth0, self.tooth1], [-1, 1]):
            for attr in ['outside_radius', 'min_r_cont']:
                res += linecirc_intersec(x1=0, y1=0, x2=prv_x, y2=prv_y, cntr_x=tooth.pitch_radius * sign, cntr_y=0,
                                         radlen=getattr(tooth, attr))
        res_arr = np.array(res).reshape(int(len(res) / 2), 2)
        y_es = res_arr[:, 1]
        pos_y_pts = res_arr[np.nonzero(y_es >= 0)[0]]
        neg_y_pts = res_arr[np.nonzero(y_es <= 0)[0]]
        pos_y = pos_y_pts[:, 1]
        neg_y = neg_y_pts[:, 1]
        min_pos = pos_y_pts[np.argmin(pos_y)]
        max_neg = neg_y_pts[np.argmax(neg_y)]
        action_line_data = np.transpose(np.vstack((min_pos, max_neg)))
        return action_line_data  # [[x0, x1], [y0, y1]]

    def get_contact_points(self, action_line_data_idx: int, progress: float) -> npt.NDArray:
        action_line_data = getattr(self, f'action_line{action_line_data_idx}data')
        pt0, pt1 = action_line_data[:, 0], action_line_data[:, 1]
        uv = get_unit_vector(pt1 - pt0)
        st = -np.linalg.norm(pt0)  # type: ignore[attr-defined]
        en = np.linalg.norm(pt1)  # type: ignore[attr-defined]
        pt_range = seedrange(st, en, self.base_step * progress, self.base_step)
        x_es = pt_range * uv[0]
        y_es = pt_range * uv[1]
        return np.vstack((x_es, y_es))  # [[x_es...], [y_es...]]

    def get_data(self) -> tuple[npt.NDArray, npt.NDArray]:
        contacts0_data = self.get_contact_points(0, self.clock.progress - self.tooth0.shift_percent)
        contacts1_data = self.get_contact_points(1, self.clock.progress - self.tooth1.shift_percent + 0.5)
        return contacts0_data, contacts1_data

    def __str__(self) -> str:
        return f'Average contact points number = {sci_round(self.ave_contact_points, 6)}\n'


class Rack:
    """Animated rack"""

    def __init__(self, module: float, pressure_angle_rad: float = STANDARD_PRESSURE_ANGLE,
                 ad_coef: float = STANDARD_ADDENDUM_COEF, de_coef: float = STANDARD_DEDENDUM_COEF,
                 profile_shift_coef: float = 0) -> None:
        self.circular_pitch = module * np.pi
        self.dedendum = de_coef * module
        self.addendum = ad_coef * module
        profile_shift = profile_shift_coef * module
        tan_pressure_angle = np.tan(pressure_angle_rad)
        y_proj_de = (self.dedendum + profile_shift) * tan_pressure_angle
        y_proj_ad = (self.addendum - profile_shift) * tan_pressure_angle
        self.seeds = [y_proj_de - self.circular_pitch / 2, -y_proj_de, y_proj_ad, -y_proj_ad + self.circular_pitch / 2]
        self.x_vals = np.array([-self.dedendum, -self.dedendum, self.addendum, self.addendum])
        self.clock = Clock()

        # Set default boundaries
        self.st = -self.circular_pitch * 2
        self.en = self.circular_pitch * 2

    def set_smart_boundaries(self, tooth0: HalfTooth, tooth1: HalfTooth) -> None:
        """
        Set boundaries depending on the mating gears.

        Args:
            tooth0: Gear 0.
            tooth1: Gear 1.

        Returns:
            None.
        """
        intersection_pt0 = np.sqrt(np.square(tooth0.outside_radius) - np.square(tooth0.pitch_radius - self.dedendum))
        intersection_pt1 = np.sqrt(np.square(tooth1.outside_radius) - np.square(tooth1.pitch_radius - self.addendum))
        offset_coef = max(tooth0.tooth_num, tooth1.tooth_num) / 32
        lim = max(intersection_pt0, intersection_pt1) + offset_coef * self.circular_pitch
        self.st, self.en = -lim, lim

    def get_limits(self) -> tuple[float, float, float, float]:
        """
        Get the curve boundaries

        Returns:
            min_x, min_y, max_x, max_y
        """
        return -self.dedendum, self.st, self.addendum, self.en

    def get_data(self) -> npt.NDArray:
        # Generate y values within the range
        pt_sets = [seedrange(self.st - self.circular_pitch, self.en + self.circular_pitch,
                             seed - self.clock.progress * self.circular_pitch, self.circular_pitch)
                   for seed in self.seeds]

        length = max([len(pt_set) for pt_set in pt_sets])

        # Augment with NaNs, and convert the list of arrays into 2d array.
        pt_sets_arr = np.array([pt_set if len(pt_set) == length else np.append(pt_set, np.nan)
                                for pt_set in pt_sets])

        # Sort sub arrays
        rot_val = -np.argmin(pt_sets_arr[:, 0])
        y_es = np.transpose(np.roll(pt_sets_arr, rot_val, axis=0)).flatten()

        # Masking the values
        mask = ~np.isnan(y_es)  # Mask to reject NaNs and extra values
        x_es = np.tile(np.roll(self.x_vals, rot_val), length)[mask]
        y_es = y_es[mask]

        # Stripping extra length
        data = np.vstack((x_es, y_es))
        i_st = np.searchsorted(y_es, self.st, side='right')
        i_en = np.searchsorted(y_es, self.en)
        data[:, i_st - 1] = lineline_intersec(x_es[i_st - 1], y_es[i_st - 1], x_es[i_st], y_es[i_st],
                                              0, self.st, 1, self.st)
        data[:, i_en] = lineline_intersec(x_es[i_en - 1], y_es[i_en - 1], x_es[i_en], y_es[i_en],
                                          0, self.en, 1, self.en)
        return data[:, i_st - 1: i_en + 1]


def stack_curves(*curves) -> npt.NDArray:
    """
    Joins the sequence of curves.

    Args:
        *curves: A curve is 2d array of points [[x_es...], [y_es...]].

    Returns:
        Stacked curves. Terminal points of adjacent curves are supposed to be the same, so the duplicates are removed.
    """
    return np.hstack(tuple([line[:, 1:] if idx else line for idx, line in enumerate(curves)]))


def populate_circ(in_x: npt.NDArray, in_y: npt.NDArray, num: int) -> npt.NDArray:
    """
    Multiply points and place them around the origin.

    Args:
        in_x: Points, x values.
        in_y: Points, y values.
        num: Number of copies, including the original one.

    Returns:
        Resulting x and y values respectively.
    """
    angle_step = 2 * np.pi / num
    curves = [rotate(in_x, in_y, angle_step * i) for i in range(num)]
    return stack_curves(*curves)
