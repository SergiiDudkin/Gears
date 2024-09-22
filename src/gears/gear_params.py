import numpy as np

from .helpers import replace_batch
from .helpers import round_float_only

STANDARD_PRESSURE_ANGLE = np.deg2rad(20)
STANDARD_ADDENDUM_COEF = 1
STANDARD_DEDENDUM_COEF = 1.25


class GearParams:
    """Set of gear params."""

    def __init__(self, tooth_num: int, module: float, pressure_angle: float = STANDARD_PRESSURE_ANGLE,
                 ad_coef: float = STANDARD_ADDENDUM_COEF, de_coef: float = STANDARD_DEDENDUM_COEF) -> None:
        """
        Computes the missing gear params from the given ones.

        Args:
            tooth_num: Number of teeth
            module: Gear module, mm.
            pressure_angle: Pressure angle, rad.
            ad_coef: Addendum coefficient, i.e. addendum / module.
            de_coef: Dedendum coefficient, i.e. dedendum / module.
        """
        self.tooth_num = tooth_num
        self.module = module
        self.pressure_angle = pressure_angle
        self.pressure_angle_ = np.rad2deg(pressure_angle)
        self.ad_coef = ad_coef
        self.de_coef = de_coef

        self.attrs_to_print = [('tooth_num', ''), ('module', ''), ('pressure_angle_', 'deg'), ('ad_coef', ''),
                               ('de_coef', ''), ('pitch_diameter', 'mm'), ('outside_diameter', 'mm'),
                               ('root_diameter', 'mm'), ('base_diameter', 'mm'), ('addendum', 'mm'), ('dedendum', 'mm')]
        self.str_to_replace = [('_', ' '), ('ad coef', 'addendum coeficient'), ('de coef', 'dedendum coeficient')]

        self._calc_pitch_diameter()
        self._calc_addendum()
        self._calc_outside_diameter()
        self._calc_dedendum()
        self._calc_root_diameter()
        self._calc_base_diameter()
        self._calc_tooth_angle()
        self._calc_circular_pitch()

    def _calc_pitch_diameter(self) -> None:
        self.pitch_diameter = self.tooth_num * self.module
        self.pitch_radius = self.pitch_diameter / 2

    def _calc_addendum(self) -> None:
        self.addendum = self.module * self.ad_coef

    def _calc_outside_diameter(self) -> None:
        self.outside_diameter = self.pitch_diameter + self.addendum * 2
        self.outside_radius = self.outside_diameter / 2

    def _calc_dedendum(self) -> None:
        self.dedendum = self.module * self.de_coef

    def _calc_root_diameter(self) -> None:
        self.root_diameter = self.pitch_diameter - self.dedendum * 2
        self.root_radius = self.root_diameter / 2

    def _calc_base_diameter(self) -> None:
        self.base_diameter = self.pitch_diameter * np.cos(self.pressure_angle)
        self.base_radius = self.base_diameter / 2

    def _calc_tooth_angle(self) -> None:
        self.tooth_angle = 2 * np.pi / self.tooth_num

    def _calc_circular_pitch(self) -> None:
        self.circular_pitch = self.module * np.pi

    def __str__(self) -> str:
        output = '\n'.join([f'{replace_batch(attr, self.str_to_replace).ljust(21)}'
                            f'{str(round_float_only(getattr(self, attr), 6)).rjust(10)} '
                            f'{unit}'
                            for attr, unit in self.attrs_to_print])
        return output
