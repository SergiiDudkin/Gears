import numpy as np

STANDARD_PRESSURE_ANGLE = 20 / 360 * 2 * np.pi  # 20 deg in rads
STANDARD_ADDENDUM_COEF = 1
STANDARD_DEDENDUM_COEF = 1.25


def get_pitch_diameter(module, tooth_num):
    return module * tooth_num


def get_addendum(module, ad_coef):
    return module * ad_coef


def get_outside_diameter(pitch_diameter, addendum):
    return pitch_diameter + addendum * 2


def get_dedendum(module, de_coef):
    return module * de_coef


def get_root_diameter(pitch_diameter, dedendum):
    return pitch_diameter - dedendum * 2


def get_base_diameter(pitch_diameter, pressure_angle):
    return pitch_diameter * np.cos(pressure_angle)


def get_gear_params(module, tooth_num, pressure_angle=STANDARD_PRESSURE_ANGLE, ad_coef=1, de_coef=1):
    pitch_diameter = get_pitch_diameter(module, tooth_num)
    addendum = get_addendum(module, ad_coef)
    outside_diameter = get_outside_diameter(pitch_diameter, addendum)
    dedendum = get_dedendum(module, de_coef)
    root_diameter = get_root_diameter(pitch_diameter, dedendum)
    base_diameter = get_base_diameter(pitch_diameter, pressure_angle)
    return pitch_diameter, outside_diameter, root_diameter, base_diameter, addendum, dedendum


def print_gear_params(pitch_diameter, outside_diameter, root_diameter, base_diameter, addendum, dedendum):
    arg_names = print_gear_params.__code__.co_varnames[:print_gear_params.__code__.co_argcount]
    for arg_name in arg_names:
        print(f'{arg_name}: {locals()[arg_name]}')
        if '_diameter' in arg_name:
            val_name = arg_name.replace('_diameter', '_radius')
            print(f'{val_name}: {locals()[arg_name] / 2}')


class GearParams:
    def __init__(self, tooth_num, module, pressure_angle=STANDARD_PRESSURE_ANGLE, ad_coef=STANDARD_ADDENDUM_COEF,
                 de_coef=STANDARD_DEDENDUM_COEF):
        self.tooth_num = tooth_num
        self.module = module
        self.pressure_angle = pressure_angle
        self.ad_coef = ad_coef
        self.de_coef = de_coef

        self._calc_pitch_diameter()
        self._calc_addendum()
        self._calc_outside_diameter()
        self._calc_dedendum()
        self._calc_root_diameter()
        self._calc_base_diameter()

        self.attrs_to_print = ['pitch_diameter', 'outside_diameter', 'root_diameter', 'base_diameter', 'addendum',
                               'dedendum']

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

    def diameters_to_radii(self):
        dict_of_attrs = self.__dict__.copy()
        for key, val in dict_of_attrs.items():
            if 'diameter' in key:
                new_attr_name = key.replace('diameter', 'radius')
                setattr(self, new_attr_name, val / 2)
                self.attrs_to_print.append(new_attr_name)

    def __str__(self):
        return '\n'.join([f'{attr}: {getattr(self, attr)}' for attr in self.attrs_to_print])
