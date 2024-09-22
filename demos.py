from plots import multiple_plot
from src.gears import HalfTooth


demo_tooth = HalfTooth(tooth_num=18, module=10.0, pressure_angle_rad=0.3490658503988659, ad_coef=1.0, de_coef=1.0,
                       profile_shift_coef=0.0, cutter_teeth_num=18, resolution=0.2, tolerance=0.1)

data = [(demo_tooth.points_outside, 'outside circle'),
        (demo_tooth.points_root, 'root circle'),
        (demo_tooth.points_epitrochoid, 'epitrochoid'),
        (demo_tooth.points_involute, 'involute')]

multiple_plot(data, title='Tooth structure', marker='o', markersize=2)
