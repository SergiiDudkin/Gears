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
