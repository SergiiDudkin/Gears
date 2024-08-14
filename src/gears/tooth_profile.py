from typing import Any
from typing import Callable
from typing import cast
from typing import Iterator

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
from .helpers import linecirc_intersec
from .helpers import sci_round
from .transforms import cartesian_to_polar
from .transforms import equidistant
from .transforms import is_within_ang
from .transforms import mirror
from .transforms import polar_to_cartesian
from .transforms import populate_circ
from .transforms import rotate
from .transforms import stack_curves
from .transforms import upd_xy_lims

STEP = 0.1
TOLERANCE = 0.1


class HalfTooth(GearParams):
    """Computation of half tooth profile using given parameters."""

    min_r_cont: float  # Min radius where the involute-involute contact with the cutter takes place

    def __init__(self, tooth_num: int, module: float, cutter_teeth_num: int = 0,
                 pressure_angle: float = STANDARD_PRESSURE_ANGLE, ad_coef: float = STANDARD_ADDENDUM_COEF,
                 de_coef: float = STANDARD_DEDENDUM_COEF, step: float = STEP, tolerance: float = TOLERANCE,
                 profile_shift_coef: float = 0) -> None:
        super().__init__(tooth_num, module, pressure_angle, ad_coef, de_coef)
        self.cutter_teeth_num = cutter_teeth_num
        self.profile_shift_coef = profile_shift_coef
        self.step = step
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
        ang_outside -= profile_ang_shift

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
            involute_t_min, epitrochoid_t_max = self._find_involute_epitrochoid_contact(invol_epitr_rad)
            self.min_r_cont = invol_epitr_rad

            # Gather limits of curves
        self.involute_lims = (involute_t_min, t_outside)
        self.epitrochoid_lims = (0, epitrochoid_t_max)
        self.outside_circle_lims = (ang_outside - ang_pitch, self.quater_angle)
        self.root_circle_lims = (-self.quater_angle, -epitrochoid_shift_ang)

    def _calc_shift_ang(self, radial_shift: float) -> float:
        proj_onto_rack = radial_shift * np.tan(self.pressure_angle)
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
            Radius and angle in polar coordinate system
        """
        invol_epitr_rad = np.sqrt((self.dedendum / np.tan(self.pressure_angle)) ** 2 + self.root_radius ** 2)
        invol_epitr_angle = np.pi / 2 - np.arccos(self.root_radius / invol_epitr_rad) + self.pressure_angle
        return invol_epitr_rad, invol_epitr_angle

    def _calc_invol_epitr(self) -> tuple[float, float]:
        """
        Finds the transition point between involute and epitrochoid.

        Returns:
            Radius and angle in polar coordinate system
        """
        # Solve the first triangle using the law of sines
        b = self.cutter_teeth_num * self.module / 2  # Cutting gear pitch radius
        a = b + self.dedendum
        alpha = np.pi / 2 + self.pressure_angle
        R2t = a / np.sin(alpha)  # Radius of the triangle's circumcircle times 2
        beta = np.arcsin(b / R2t)  # Angle beta is guarantied to be acute
        gamma = np.pi - alpha - beta
        c = R2t * np.sin(gamma)

        # Solve the second triangle using the law of cosines
        c_ = c
        b_ = self.pitch_radius
        alpha_ = np.pi / 2 - self.pressure_angle
        a_ = np.sqrt(b_ ** 2 + c_ ** 2 - 2 * b_ * c_ * np.cos(alpha_))
        beta_ = np.arccos((a_ ** 2 + c_ ** 2 - b_ ** 2) / (2 * a_ * c_))
        invol_epitr_rad, invol_epitr_angle = a_, beta_
        return invol_epitr_rad, invol_epitr_angle

    def _find_involute_epitrochoid_contact(self, invol_epitr_rad: float) -> tuple[float, float]:
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
        points_involute = equidistant(involute, self.involute_lims, self.step, self.tolerance, **self.involute_params)
        points_epitrochoid = equidistant(self.my_epitrochoid, self.epitrochoid_lims,
                                         self.step, self.tolerance, **self.epitrochoid_params)
        points_outside = equidistant(circle, self.outside_circle_lims, self.step,
                                     self.tolerance, **self.outside_circle_params)
        points_root = equidistant(circle, self.root_circle_lims, self.step, self.tolerance, **self.root_circle_params)

        self.half_tooth_profile = stack_curves(points_root, points_epitrochoid, points_involute, points_outside)

    def get_curves_data(self) -> dict[str, dict[str, Any]]:
        return {
            'involute': {
                'x': 'r * (np.cos(t_) + t * np.sin(t_))',
                'y': 'r * (np.sin(t_) - t * np.cos(t_))',
                't_': 't + a0',
                'params': self.involute_params,
                'lims': self.involute_lims
            },
            'epitrochoid': {
                'x': '(R - l) * np.cos(t_) + t * R * np.sin(t_)' if self.is_rack else
                '(R + r) * np.cos(t_) - d * np.cos(R * t / r + t_)',
                'y': '(R - l) * np.sin(t_) - t * R * np.cos(t_)' if self.is_rack else
                '(R + r) * np.sin(t_) - d * np.sin(R * t / r + t_)',
                't_': 't + a0',
                'params': self.epitrochoid_params,
                'lims': self.epitrochoid_lims
            },
            'outside circle': {
                'x': 'r * np.cos(t)',
                'y': 'r * np.sin(t)',
                'params': self.outside_circle_params,
                'lims': self.outside_circle_lims
            },
            'root circle': {
                'x': 'r * np.cos(t)',
                'y': 'r * np.sin(t)',
                'params': self.root_circle_params,
                'lims': self.root_circle_lims
            }
        }

    def __str__(self) -> str:
        output = super().__str__()
        curves_data = self.get_curves_data()
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
    def __init__(self, halftooth0: HalfTooth, halftooth1: HalfTooth, step_cnt: int = 100,
                 sector: tuple[float, float] = (0, np.pi), rot_ang: float = 0, is_acw: bool = False) -> None:
        self.ht0 = halftooth0
        self.ht1 = halftooth1
        self.step_cnt = step_cnt
        self.sec_st, self.sec_en = sector
        self.rot_ang = rot_ang
        self.is_acw = is_acw

        self.i = self.step_cnt - 1
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

    def __iter__(self) -> Iterator[npt.NDArray]:
        ang_step = self.ht0.tooth_angle / self.step_cnt
        dir_ = self.is_acw * 2 - 1  # Bool to sign
        while True:
            self.i = (self.i + 1) % self.step_cnt
            yield self.get_sector_profile(self.sec_st, self.sec_en, (ang_step * self.i + self.rot_ang) * dir_)

    def get_limits(self) -> tuple[float, float, float, float]:
        xy_lims = (float('inf'), float('inf'), float('-inf'), float('-inf'))
        for ang in (self.sec_st, self.sec_en):
            for rad in (self.ht0.root_radius, self.ht0.outside_radius):
                x, y = polar_to_cartesian(ang, rad)
                xy_lims = upd_xy_lims(x, y, *xy_lims)
        for i, (x, y) in enumerate([(1, 0), (0, 1), (-1, 0), (0, -1)]):
            if is_within_ang(i * np.pi / 2, self.sec_st, self.sec_en):
                xy_lims = upd_xy_lims(x * self.ht0.outside_radius, y * self.ht0.outside_radius, *xy_lims)
        return xy_lims


def get_action_line(tooth0: HalfTooth, tooth1: HalfTooth) -> npt.NDArray:
    prv_x, prv_y = rotate(0, 1, tooth0.pressure_angle)
    res: list[float] = []
    for tooth, sign in zip([tooth0, tooth1], [-1, 1]):
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
    return action_line_data
