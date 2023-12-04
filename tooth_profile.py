import numpy as np
from transforms import make_angrad_func, mirror, populate_circ, equidistant, stack_curves, is_within_ang
from curves import circle, involute, epitrochoid, epitrochoid_flat
from gear_params import GearParams, STANDARD_PRESSURE_ANGLE, STANDARD_ADDENDUM_COEF, STANDARD_DEDENDUM_COEF

STEP = 0.1
TOLERANCE = 0.1


class Tooth(GearParams):
    def __init__(self, tooth_num, module, cutter_teeth_num=float('inf'), pressure_angle=STANDARD_PRESSURE_ANGLE,
                 ad_coef=STANDARD_ADDENDUM_COEF, de_coef=STANDARD_DEDENDUM_COEF, step=STEP, tolerance=TOLERANCE):
        super().__init__(tooth_num, module, pressure_angle, ad_coef, de_coef)
        self.cutter_teeth_num = cutter_teeth_num
        self.step = step
        self.tolerance = tolerance
        self.diameters_to_radii()
        self._calc_invol_epitr_flat()
        self._build_half_tooth()

    def _calc_invol_epitr_flat(self):
        self.invol_epitr_rad = np.sqrt((self.dedendum / np.tan(self.pressure_angle)) ** 2 + self.root_radius ** 2)
        self.invol_epitr_angle = np.pi / 2 - np.arccos(self.root_radius / self.invol_epitr_rad) + self.pressure_angle

    def _calc_invol_epitr(self):
        # Solve the first triangle using law of sines
        b = self.cutter_teeth_num * self.module / 2  # Cutting gear pitch radius
        a = b + self.dedendum
        alpha = np.pi / 2 + self.pressure_angle
        R2t = a / np.sin(alpha)
        beta = np.arcsin(b / R2t)  # Angle beta is guarantied to be acute
        gamma = np.pi - alpha - beta
        c = R2t * np.sin(gamma)

        # Solve the second triangle using law of cosines
        c_ = c
        b_ = self.pitch_radius
        alpha_ = np.pi / 2 - self.pressure_angle
        a_ = np.sqrt(b_ ** 2 + c_ ** 2 - 2 * b_ * c_ * np.cos(alpha_))
        self.invol_epitr_rad = a_

        # Find angle using law of cosines
        beta_ = np.arccos((a_ ** 2 + c_ ** 2 - b_ ** 2) / (2 * a_ * c_))
        self.invol_epitr_angle = beta + beta_

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
        self.tooth_angle = 2 * np.pi / self.tooth_num
        self.quater_angle = self.tooth_angle / 4

        # Get points of involute
        involute_points = self._get_involute_points()
        ang_inv_epitr = involute_points[0][0]
        t_inv_epitr = involute_points[0][3]
        ang_pitch = involute_points[1][0]
        t_outside = involute_points[2][3]
        ang_outside = involute_points[2][0]
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

    def get_tooth_profile(self):
        seg_st = np.array([0, 0])
        seg_en = np.array([np.cos(-self.quater_angle), np.sin(-self.quater_angle)])
        reflected = np.transpose([mirror(point, seg_st, seg_en) for point in np.transpose(self.half_tooth_profile)])
        return stack_curves(reflected[:, ::-1], self.half_tooth_profile)

    def get_gear_profile(self):
        """Returns the entire gear profile"""
        return populate_circ(*self.get_tooth_profile(), self.tooth_num)

    def get_sector_profile(self, sec_st, sec_en):
        # Angular borders. Tooth n lies in between borders[n-1] and borders[n].
        borders = np.remainder(self.quater_angle + self.tooth_angle * np.arange(self.tooth_num), np.pi * 2)
        borders = np.where(borders <= np.pi, borders, borders - 2 * np.pi)

        borders_in_sector = is_within_ang(borders, sec_st, sec_en)

        seg_st_within_tooth, seg_en_within_tooth = [np.array([is_within_ang(seg_edge, tooth_st, tooth_en)
                                                              for tooth_st, tooth_en
                                                              in zip(np.roll(borders, 1), borders)], dtype=np.uint8)
                                                    for seg_edge in [sec_st, sec_en]]

        integer_teeth = np.logical_not(seg_st_within_tooth | seg_en_within_tooth)
        full_teeth = np.roll(borders_in_sector, 1) & borders_in_sector & integer_teeth
        empty_teeth = np.logical_not(np.roll(borders_in_sector, 1) | borders_in_sector) & integer_teeth

        print(borders)
        print(full_teeth.astype(np.uint8))
        print(empty_teeth.astype(np.uint8))
        print(seg_st_within_tooth)
        print(seg_en_within_tooth)
