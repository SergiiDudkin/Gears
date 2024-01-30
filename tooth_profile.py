import numpy as np
from transforms import make_angrad_func, mirror, populate_circ, equidistant, stack_curves, is_within_ang, rotate, cartesian_to_polar, polar_to_cartesian, upd_xy_lims, line_line_intersection
from curves import circle, involute, epitrochoid, epitrochoid_flat
from gear_params import GearParams, STANDARD_PRESSURE_ANGLE, STANDARD_ADDENDUM_COEF, STANDARD_DEDENDUM_COEF

STEP = 0.1
TOLERANCE = 0.1


class HalfTooth(GearParams):
    def __init__(self, tooth_num, module, cutter_teeth_num=float('inf'), pressure_angle=STANDARD_PRESSURE_ANGLE,
                 ad_coef=STANDARD_ADDENDUM_COEF, de_coef=STANDARD_DEDENDUM_COEF, step=STEP, tolerance=TOLERANCE):
        super().__init__(tooth_num, module, pressure_angle, ad_coef, de_coef)
        self.cutter_teeth_num = cutter_teeth_num
        self.step = step
        self.tolerance = tolerance
        self._calc_invol_epitr_flat()
        print(f'self.invol_epitr_rad: {self.invol_epitr_rad}')
        print(f'self.invol_epitr_angle: {np.rad2deg(self.invol_epitr_angle)}')
        print(f'self.base_radius: {self.base_radius}')
        # print(180 - (np.rad2deg(self.invol_epitr_angle) + (90 - np.rad2deg(self.pressure_angle))))
        self._calc_epitrochoid_shift_ang()
        self.involute_epitrochoid_intersection_demo()
        self._find_involute_epitrochoid_intersection()
        # self._build_half_tooth()

    def _calc_invol_epitr_flat(self):
        self.invol_epitr_rad = np.sqrt((self.dedendum / np.tan(self.pressure_angle)) ** 2 + self.root_radius ** 2)
        self.invol_epitr_angle = np.pi / 2 - np.arccos(self.root_radius / self.invol_epitr_rad) + self.pressure_angle  # ToDo: Use it as tooth undercut detector (if < pi / 2).

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
        self.invol_epitr_rad = a_
        beta_ = np.arccos((a_ ** 2 + c_ ** 2 - b_ ** 2) / (2 * a_ * c_))
        self.invol_epitr_angle = beta  # ToDo: Use it as tooth undercut detector (if < pi / 2).

    def _get_involute_points(self):
        self.involute_angrad = make_angrad_func(involute)
        return [self.involute_angrad(rad, 0, 2, self.base_radius) for rad in (self.invol_epitr_rad, self.pitch_radius,
                                                                              self.outside_radius)]

    def _get_epitrochoid_flat_point(self):
        self.epitrochoid_flat_angrad = make_angrad_func(epitrochoid_flat)
        return self.epitrochoid_flat_angrad(self.invol_epitr_rad, 0, 2, self.pitch_radius, self.dedendum)

    def _get_epitrochoid_point(self):
        self.epitrochoid_angrad = make_angrad_func(epitrochoid)
        pitch_radius2 = self.cutter_teeth_num * self.module / 2  # Cutting gear pitch radius
        return self.epitrochoid_angrad(self.invol_epitr_rad, 0, 2, self.pitch_radius, pitch_radius2, pitch_radius2 +
                                       self.dedendum)

    def _build_half_tooth(self):
        self.quater_angle = self.tooth_angle / 4

        # Get points of involute
        involute_points = self._get_involute_points()
        ang_inv_epitr = involute_points[0][0]
        t_inv_epitr = involute_points[0][3]
        ang_pitch = involute_points[1][0]
        t_outside = involute_points[2][3]
        ang_outside = involute_points[2][0]
        # print(f'ang_outside - ang_pitch: {ang_outside - ang_pitch}')
        points_involute = equidistant(involute, t_inv_epitr, t_outside, self.step, self.tolerance, r=self.base_radius,
                                      a0=-ang_pitch)

        # Get points of epitrochoid flat
        ang_epitr_inv, x, y, t_epitr_inv = self._get_epitrochoid_flat_point()
        rot_ang = ang_epitr_inv + ang_inv_epitr - ang_pitch
        points_epitrochoid_flat = equidistant(epitrochoid_flat, 0, -t_epitr_inv, self.step, self.tolerance,
                                              R=self.pitch_radius, l=self.dedendum, a0=rot_ang)

        # Get points of outside circle
        points_outside = equidistant(circle, ang_outside - ang_pitch, self.quater_angle, self.step, self.tolerance,
                                     r=self.outside_radius, a0=0)

        # Get points of root circle
        points_root = equidistant(circle, -self.quater_angle, rot_ang, self.step, self.tolerance,
                                  r=self.root_radius, a0=0)

        self.half_tooth_profile = stack_curves(points_root, points_epitrochoid_flat, points_involute, points_outside)

    def _calc_epitrochoid_shift_ang(self):
        involute_angrad = make_angrad_func(involute)  # ToDo: This function should be global.

        gear_ratio = self.cutter_teeth_num / self.tooth_num
        cutter_base_radius = self.base_radius * gear_ratio
        self.cutter_pitch_radius = self.pitch_radius * gear_ratio
        self.cutter_outside_radius = self.cutter_pitch_radius + self.dedendum
        # print(f'''
        # self.pitch_radius: {self.pitch_radius}
        # cutter_base_radius: {cutter_base_radius}
        # cutter_pitch_radius: {cutter_pitch_radius}
        # cutter_outside_radius: {cutter_outside_radius}
        # ''')

        pitch_ang = involute_angrad(self.cutter_pitch_radius, 0, 2, cutter_base_radius)[0]
        outside_ang = involute_angrad(self.cutter_outside_radius, 0, 2, cutter_base_radius)[0]
        self.epitrochoid_shift_ang = (outside_ang - pitch_ang) * gear_ratio
        print(f'self.epitrochoid_shift_ang: {self.epitrochoid_shift_ang}')

    def involute_epitrochoid_intersection_demo(self):
        # Get points of involute
        involute_points = self._get_involute_points()
        ang_pitch = involute_points[1][0]
        t_outside = involute_points[2][3]
        self._set_involute_params(r=self.base_radius, a0=-ang_pitch)
        self.raw_involute = equidistant(involute, 0, t_outside, self.step, self.tolerance, **self.involute_params)

        rot_ang = -self.epitrochoid_shift_ang
        self._set_epitrochoid_params(R=self.pitch_radius, r=self.cutter_pitch_radius, d=self.cutter_outside_radius,
                                     a0=rot_ang)
        self.raw_epitrochoid = equidistant(epitrochoid, 0, -1, self.step, self.tolerance, **self.epitrochoid_params)
# epitrochoid(t, R, r, d, a0=0)

    def _set_involute_params(self, r, a0):
        self.involute_params = {
            'r': r,
            'a0': a0
        }

    def _set_epitrochoid_params(self, R, r, d, a0):
        self.epitrochoid_params = {
            'R': R,
            'r': r,
            'd': d,
            'a0': a0
        }

    def _find_involute_epitrochoid_intersection(self):
        involute_angrad = make_angrad_func(involute)  # ToDo: This function should be global.
        epitrochoid_angrad = make_angrad_func(epitrochoid)  # ToDo: This function should be global.
        ang, x, y, t_curr = epitrochoid_angrad(self.outside_radius, 0, -2, **self.epitrochoid_params)
        print(f'rad: {self.outside_radius}, ang: {ang}, x: {x}, y: {y}, t_curr: {t_curr}')
        r_min = self.base_radius
        r_max = self.outside_radius

        for _ in range(100):
            # print(f'_: {_}')
            # xy0 = np.array(involute_angrad(r_min, 0, 1, **self.involute_params)[1:3])
            # xy1 = np.array(involute_angrad(r_max, 0, 1, **self.involute_params)[1:3])
            # xy2 = np.array(epitrochoid_angrad(r_min, 0, -1, **self.epitrochoid_params)[1:3])
            # xy3 = np.array(epitrochoid_angrad(r_max, 0, -1, **self.epitrochoid_params)[1:3])
            # xy_intersection_pt = line_line_intersection(xy0, xy1, xy2, xy3)
            # r_curr = cartesian_to_polar(*xy_intersection_pt)[1]
            # if not (r_min < r_curr < r_max):
            #     r_curr = np.mean([r_min, r_max])
            r_curr = np.mean([r_min, r_max])
            involute_ang = involute_angrad(r_curr, 0, 1, **self.involute_params)[0]
            epitrochoid_ang = epitrochoid_angrad(r_curr, 0, -1, **self.epitrochoid_params)[0]
            if involute_ang == epitrochoid_ang or not (r_min < r_curr < r_max):
                break
            if involute_ang < epitrochoid_ang:
                r_min = r_curr
            else:
                r_max = r_curr
        else:
            print('!!! WARNING! Number of iteration exceeded the limit.')

        # print(f'x: {xy_intersection_pt[0]}, y: {xy_intersection_pt[1]}')
        print(f'involute_ang: {involute_ang}, epitrochoid_ang: {epitrochoid_ang}')
        print(f'r_min {r_min}, r_curr {r_curr}, r_max {r_max}')
        print(polar_to_cartesian(involute_ang, r_curr))

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
