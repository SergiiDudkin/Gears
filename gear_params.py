import numpy as np

STANDARD_PRESSURE_ANGLE = 20 / 360 * 2 * np.pi  # 20 deg in rads
STANDARD_ADDENDUM_COEF = 1
STANDARD_DEDENDUM_COEF = 1.25


class GearParams:
    pitch_radius: float
    outside_radius: float
    root_radius: float
    base_radius: float

    def __init__(self, tooth_num, module, pressure_angle=STANDARD_PRESSURE_ANGLE, ad_coef=STANDARD_ADDENDUM_COEF,
                 de_coef=STANDARD_DEDENDUM_COEF):
        self.tooth_num = tooth_num
        self.module = module
        self.pressure_angle = pressure_angle
        self.ad_coef = ad_coef
        self.de_coef = de_coef

        self.attrs_to_print = ['pitch_diameter', 'outside_diameter', 'root_diameter', 'base_diameter', 'addendum',
                               'dedendum']

        self._calc_pitch_diameter()
        self._calc_addendum()
        self._calc_outside_diameter()
        self._calc_dedendum()
        self._calc_root_diameter()
        self._calc_base_diameter()
        self._calc_tooth_angle()
        self._diameters_to_radii()

    def _calc_pitch_diameter(self):
        self.pitch_diameter = self.tooth_num * self.module

    def _calc_addendum(self):
        self.addendum = self.module * self.ad_coef

    def _calc_outside_diameter(self):
        self.outside_diameter = self.pitch_diameter + self.addendum * 2

    def _calc_dedendum(self):
        self.dedendum = self.module * self.de_coef

    def _calc_root_diameter(self):
        self.root_diameter = self.pitch_diameter - self.dedendum * 2

    def _calc_base_diameter(self):
        self.base_diameter = self.pitch_diameter * np.cos(self.pressure_angle)

    def _calc_tooth_angle(self):
        self.tooth_angle = 2 * np.pi / self.tooth_num

    def _diameters_to_radii(self):
        dict_of_attrs = self.__dict__.copy()
        for key, val in dict_of_attrs.items():
            if 'diameter' in key:
                new_attr_name = key.replace('diameter', 'radius')
                setattr(self, new_attr_name, val / 2)
                self.attrs_to_print.append(new_attr_name)

    def __str__(self):
        return '\n'.join([f'{attr}: {getattr(self, attr)}' for attr in self.attrs_to_print])
