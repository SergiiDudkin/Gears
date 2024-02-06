import numpy as np
from transforms import mirror, populate_circ, equidistant, stack_curves, is_within_ang, rotate, cartesian_to_polar, polar_to_cartesian, upd_xy_lims
from curves import circle, involute, epitrochoid, epitrochoid_flat, involute_angrad, epitrochoid_angrad, epitrochoid_flat_angrad
from gear_params import GearParams, STANDARD_PRESSURE_ANGLE, STANDARD_ADDENDUM_COEF, STANDARD_DEDENDUM_COEF
from plots import simple_plot, multiple_plot

STEP = 0.1
TOLERANCE = 0.1


class HalfTooth(GearParams):
    def __init__(self, tooth_num, module, cutter_teeth_num=float('inf'), pressure_angle=STANDARD_PRESSURE_ANGLE,
                 ad_coef=STANDARD_ADDENDUM_COEF, de_coef=STANDARD_DEDENDUM_COEF, step=STEP, tolerance=TOLERANCE):
        super().__init__(tooth_num, module, pressure_angle, ad_coef, de_coef)
        self.cutter_teeth_num = cutter_teeth_num
        self.step = step
        self.tolerance = tolerance

        self.is_rack = not cutter_teeth_num
        self.my_epitrochoid = epitrochoid_flat if self.is_rack else epitrochoid
        self.my_epitrochoid_angrad = epitrochoid_flat_angrad if self.is_rack else epitrochoid_angrad

        self._calc_profile_params()
        self._build_half_tooth()

    def _calc_profile_params(self):
        self.quater_angle = self.tooth_angle / 4

        if self.is_rack:
            epitrochoid_shift_ang = self._calc_epitrochoid_flat_shift_ang()
        else:
            epitrochoid_shift_ang, cutter_pitch_radius, cutter_outside_radius = self._calc_epitrochoid_shift_ang()
        ang_pitch = involute_angrad(self.pitch_radius, 0, 2, self.base_radius)[0]
        ang_outside, _, _, t_outside = involute_angrad(self.outside_radius, 0, 2, self.base_radius)

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
            'a0': 0
        }
        self.root_circle_params = {
            'r': self.root_radius,
            'a0': 0
        }

        invol_epitr_rad, invol_epitr_angle = self._calc_invol_epitr_flat() if self.is_rack else self._calc_invol_epitr()
        if invol_epitr_angle * 2 < np.pi:
            involute_t_min, epitrochoid_t_max, r_curr = self._find_involute_epitrochoid_intersection()  # ToDo: Use r_curr or delete
        else:
            involute_t_min, epitrochoid_t_max = self._find_involute_epitrochoid_contact(invol_epitr_rad)

        # Gather limits of curves
        self.involute_lims = (involute_t_min, t_outside)
        self.epitrochoid_lims = (0, epitrochoid_t_max)
        self.outside_circle_lims = (ang_outside - ang_pitch, self.quater_angle)
        self.root_circle_lims = (-self.quater_angle, -epitrochoid_shift_ang)

    def _calc_epitrochoid_flat_shift_ang(self):
        circular_pitch = self.module * np.pi
        proj_onto_rack = self.dedendum * np.tan(self.pressure_angle)
        epitrochoid_shift_ang = self.tooth_angle * proj_onto_rack / circular_pitch
        return epitrochoid_shift_ang

    def _calc_epitrochoid_shift_ang(self):
        gear_ratio = self.cutter_teeth_num / self.tooth_num
        cutter_base_radius = self.base_radius * gear_ratio
        cutter_pitch_radius = self.pitch_radius * gear_ratio
        cutter_outside_radius = cutter_pitch_radius + self.dedendum
        pitch_ang = involute_angrad(cutter_pitch_radius, 0, 2, cutter_base_radius)[0]
        outside_ang = involute_angrad(cutter_outside_radius, 0, 2, cutter_base_radius)[0]
        epitrochoid_shift_ang = (outside_ang - pitch_ang) * gear_ratio
        return epitrochoid_shift_ang, cutter_pitch_radius, cutter_outside_radius

    def _calc_invol_epitr_flat(self):
        invol_epitr_rad = np.sqrt((self.dedendum / np.tan(self.pressure_angle)) ** 2 + self.root_radius ** 2)
        invol_epitr_angle = np.pi / 2 - np.arccos(self.root_radius / invol_epitr_rad) + self.pressure_angle
        return invol_epitr_rad, invol_epitr_angle

    def _calc_invol_epitr(self):
        # Solve the first triangle using law of sines
        b = self.cutter_teeth_num * self.module / 2  # Cutting gear pitch radius
        a = b + self.dedendum
        alpha = np.pi / 2 + self.pressure_angle
        R2t = a / np.sin(alpha)  # Radius of the triangle's circumcircle times 2
        beta = np.arcsin(b / R2t)  # Angle beta is guarantied to be acute
        gamma = np.pi - alpha - beta
        c = R2t * np.sin(gamma)

        # Solve the second triangle using law of cosines
        c_ = c
        b_ = self.pitch_radius
        alpha_ = np.pi / 2 - self.pressure_angle
        a_ = np.sqrt(b_ ** 2 + c_ ** 2 - 2 * b_ * c_ * np.cos(alpha_))
        beta_ = np.arccos((a_ ** 2 + c_ ** 2 - b_ ** 2) / (2 * a_ * c_))
        invol_epitr_rad, invol_epitr_angle = a_, beta_
        return invol_epitr_rad, invol_epitr_angle

    def _find_involute_epitrochoid_contact(self, invol_epitr_rad):
        involute_t_min = involute_angrad(invol_epitr_rad, 0, 1, **self.involute_params)[3]
        epitrochoid_t_max = self.my_epitrochoid_angrad(invol_epitr_rad, 0, -1, **self.epitrochoid_params)[3]
        return involute_t_min, epitrochoid_t_max

    def _find_involute_epitrochoid_intersection(self):
        r_min = self.base_radius
        r_max = self.outside_radius

        for _ in range(100):
            r_curr = np.mean([r_min, r_max])
            involute_ang, _, _, involute_t_min = involute_angrad(r_curr, 0, 1, **self.involute_params)
            epitrochoid_ang, _, _, epitrochoid_t_max = self.my_epitrochoid_angrad(r_curr, 0, -1, **self.epitrochoid_params)
            if involute_ang == epitrochoid_ang or not (r_min < r_curr < r_max):
                break
            if involute_ang < epitrochoid_ang:
                r_min = r_curr
            else:
                r_max = r_curr
        else:
            print('!!! WARNING! Number of iteration exceeded the limit.')

        return involute_t_min, epitrochoid_t_max, r_curr

    def _build_half_tooth(self):
        points_involute = equidistant(involute, self.involute_lims, self.step, self.tolerance, **self.involute_params)
        points_epitrochoid = equidistant(self.my_epitrochoid, self.epitrochoid_lims, self.step, self.tolerance, **self.epitrochoid_params)
        points_outside = equidistant(circle, self.outside_circle_lims, self.step, self.tolerance, **self.outside_circle_params)
        points_root = equidistant(circle, self.root_circle_lims, self.step, self.tolerance, **self.root_circle_params)

        self.half_tooth_profile = stack_curves(points_root, points_epitrochoid, points_involute, points_outside)


class GearSector:
    def __init__(self, halftooth0, halftooth1, step_cnt=100, sector=(0, np.pi), rot_ang=0, is_acw=False):
        self.ht0 = halftooth0
        self.ht1 = halftooth1
        self.step_cnt = step_cnt
        self.sec_st, self.sec_en = sector
        self.rot_ang = rot_ang
        self.is_acw = is_acw

        self.i = self.step_cnt - 1
        self._build_full_tooth()

    def _build_full_tooth(self):
        sec_st = np.array([0, 0])
        sec_en = np.array([np.cos(-self.ht0.quater_angle), np.sin(-self.ht0.quater_angle)])
        reflected = np.transpose([mirror(point, sec_st, sec_en) for point in np.transpose(self.ht1.half_tooth_profile)])
        self.full_tooth_profile = stack_curves(reflected[:, ::-1], self.ht0.half_tooth_profile)

    def get_gear_profile(self):
        """Returns the entire gear profile"""
        return populate_circ(*self.full_tooth_profile, self.ht0.tooth_num)

    def get_sector_profile(self, sec_st, sec_en, rot_ang=0):
        st_tooth_idx, full_teeth_ins, en_tooth_idx = self._sortout_teeth(sec_st, sec_en, rot_ang)

        if not full_teeth_ins.size and st_tooth_idx == en_tooth_idx:
            # Case of a single tooth within the sector
            tooth = rotate(*self.full_tooth_profile, self.ht0.tooth_angle * st_tooth_idx + rot_ang)
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
                full_tooth = rotate(*self.full_tooth_profile, self.ht0.tooth_angle * full_tooth_idx + rot_ang)
                curves.append(full_tooth)

            en_tooth = self._get_term_tooth_profile(en_tooth_idx, sec_st, sec_en, rot_ang, is_en=True)
            curves.append(en_tooth)

            sector_profile = stack_curves(*curves)

        return sector_profile

    def _sortout_teeth(self, sec_st, sec_en, rot_ang=0):
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

    def _get_term_tooth_profile(self, tooth_idx, sec_st, sec_en, rot_ang=0, is_en=False):
        tooth = rotate(*self.full_tooth_profile, self.ht0.tooth_angle * tooth_idx + rot_ang)
        tooth_ang = cartesian_to_polar(*tooth)[0]
        tooth_in_sector_bm = is_within_ang(tooth_ang, sec_st, sec_en)
        try:
            pt_idx = np.nonzero(tooth_in_sector_bm)[0][0 - is_en] + is_en
        except IndexError:
            pt_idx = -1 + is_en
        return tooth[:, :pt_idx] if is_en else tooth[:, pt_idx:]

    def __iter__(self):
        ang_step = self.ht0.tooth_angle / self.step_cnt
        dir_ = self.is_acw * 2 - 1  # Bool to sign
        while True:
            self.i = (self.i + 1) % self.step_cnt
            yield self.get_sector_profile(self.sec_st, self.sec_en, (ang_step * self.i + self.rot_ang) * dir_)

    def get_limits(self):
        xy_lims = (float('inf'), float('inf'), float('-inf'), float('-inf'))
        for ang in (self.sec_st, self.sec_en):
            for rad in (self.ht0.root_radius, self.ht0.outside_radius):
                x, y = polar_to_cartesian(ang, rad)
                xy_lims = upd_xy_lims(x, y, *xy_lims)
        for i, (x, y) in enumerate([(1, 0), (0, 1), (-1, 0), (0, -1)]):
            if is_within_ang(i * np.pi / 2, self.sec_st, self.sec_en):
                xy_lims = upd_xy_lims(x * self.ht0.outside_radius, y * self.ht0.outside_radius, *xy_lims)
        return xy_lims
