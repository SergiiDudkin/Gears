import numpy as np
from plots import simple_plot, multiple_plot
from curves import involute, epitrochoid, epitrochoid_flat
from gear_params import STANDARD_PRESSURE_ANGLE, get_gear_params, print_gear_params, GearParams
from transforms import mirror, make_angrad_func, cartesian_to_polar, populate_circ, equidistant
# from tooth_profile import get_inv_epitr_flat, get_involute_points, build_tooth, get_epitrochoid_flat_point, HalfTooth
from tooth_profile import HalfTooth

np.set_printoptions(linewidth=1000)


function = 'HalfTooth'

if function == 'involute':
    # t_s = np.arange(0, 4, 0.001)
    # r = 2
    # simple_plot(*involute(t_s, r, t0=0), 'Involute')
    # ==================================================================================================================
    t_s = np.arange(0, 4, 0.001)
    r = 2
    data0 = (involute(t_s, r, a0=0), 'a0 = 0')
    data1 = (involute(t_s, r, a0=0.5), 'a0 = 0.5')
    data2 = (involute(t_s, r, a0=1), 'a0 = 1')
    data3 = (involute(t_s, r, a0=1.5), 'a0 = 1.5')
    data4 = (involute(t_s, r, a0=2), 'a0 = 2')
    multiple_plot([data0, data1, data2, data3, data4])

if function == 'epitrochoid':
    # t_s = np.arange(-2, 2, 0.01)
    # R = 4
    # r = 2
    # d = 3
    # simple_plot(*epitrochoid(t_s, R, r, d), 'Epitrochoid')
    # ==================================================================================================================
    # t_s = np.arange(-1, 1, 0.01)
    # R = 4
    #
    # r = 2
    # d = 3
    # data0 = (epitrochoid(t_s, R, r, d), 'r = 2')
    #
    # r = 8
    # d = 9
    # data1 = (epitrochoid(t_s, R, r, d), 'r = 8')
    #
    # l = 1
    # data2 = (epitrochoid_flat(t_s, R, l), 'r = inf')
    #
    # l = 1.25
    # data3 = (epitrochoid_flat(t_s, R, l), 'l = 1.25')
    #
    # multiple_plot([data0, data1, data2, data3])
    # ==================================================================================================================
    t_s = np.arange(-1, 1, 0.01)
    R = 4
    r = 2
    d = 3
    data0 = (epitrochoid(t_s, R, r, d, a0=0), 'a0 = 0')
    data1 = (epitrochoid(t_s, R, r, d, a0=0.5), 'a0 = 0.5')
    data2 = (epitrochoid(t_s, R, r, d, a0=1), 'a0 = 1')
    data3 = (epitrochoid(t_s, R, r, d, a0=1.5), 'a0 = 1.5')
    data4 = (epitrochoid(t_s, R, r, d, a0=2), 'a0 = 2')
    multiple_plot([data0, data1, data2, data3, data4])

if function == 'epitrochoid_flat':
    # t_s = np.arange(-5, 5, 0.01)
    # R = 4
    # l = 1
    # simple_plot(*epitrochoid_flat(t_s, R, l), 'Epitrochoid (r=inf)')
    # ==================================================================================================================
    t_s = np.arange(-2, 2, 0.01)
    R = 4
    l = 1
    data0 = (epitrochoid_flat(t_s, R, l, a0=0), 'a0 = 0')
    data1 = (epitrochoid_flat(t_s, R, l, a0=0.5), 'a0 = 0.5')
    data2 = (epitrochoid_flat(t_s, R, l, a0=1), 'a0 = 1')
    data3 = (epitrochoid_flat(t_s, R, l, a0=1.5), 'a0 = 1.5')
    data4 = (epitrochoid_flat(t_s, R, l, a0=2), 'a0 = 2')
    multiple_plot([data0, data1, data2, data3, data4])


if function == 'epitrochoids_both':
    t_s = np.arange(-1, 1, 0.01)
    R = 4

    r = 2
    d = 3
    data0 = (epitrochoid(t_s, R, r, d), 'epitrochoid')

    l = d - r
    data1 = (epitrochoid_flat(t_s, R, l), 'epitrochoid_flat')

    multiple_plot([data0, data1])

if function == 'make_angrad_func':
    t = 100
    r = 2
    x, y = involute(t, r)
    ang, rad = cartesian_to_polar(x, y)
    print(f'x {x}, y {y}')
    print(f'ang {ang}, rad {rad}')

    involute_angrad = make_angrad_func(involute)
    ang_, x, y, t = involute_angrad(rad, 0, 2, 2)
    print(f'ang_ {ang_}')

if function == 'mirror':
    x_s = np.array([7, 5, 2])
    y_s = np.array([4, 6, 8])

    seg_st = np.array([5, 2])
    seg_en = np.array([-1, 3])
    refl_xs, refl_ys = list(zip(*[mirror(np.array([x, y]), seg_st, seg_en) for x, y in zip(x_s, y_s)]))

    mirr_xs, mirr_ys = list(zip(seg_st, seg_en))
    data = [((x_s, y_s), 'orig'), ((refl_xs, refl_ys), 'reflection'), ((mirr_xs, mirr_ys), 'mirror')]
    multiple_plot(data)

if function == 'populate_circ':
    x_s = np.array([7, 7, 6])
    y_s = np.array([6, 7, 7])
    # out_x, out_y = x_s, y_s
    num = 10
    out_x, out_y = populate_circ(x_s, y_s, num)
    simple_plot(out_x, out_y, title='Figure 1')

# if function == 'get_inv_epitr_flat':
#     gear_params = get_gear_params(module=10, tooth_num=100)
#     print_gear_params(*gear_params)
#     pitch_diameter, outside_diameter, root_diameter, base_diameter, addendum, dedendum = gear_params
#     inv_epitr_flat, angle = get_inv_epitr_flat(root_diameter, dedendum, STANDARD_PRESSURE_ANGLE)
#     print(f'inv_epitr_flat: {inv_epitr_flat}, angle: {angle}, {angle >= np.pi / 2}')
#     # print(inv_epitr_flat > base_diameter)
#
# if function == 'get_involute_points':
#     gear_params = get_gear_params(module=10, tooth_num=30)
#     print_gear_params(*gear_params)
#     pitch_diameter, outside_diameter, root_diameter, base_diameter, addendum, dedendum = gear_params
#     inv_epitr_flat, angle = get_inv_epitr_flat(root_diameter, dedendum, STANDARD_PRESSURE_ANGLE)
#     involute_points = get_involute_points(base_diameter, inv_epitr_flat, pitch_diameter, outside_diameter)
#     print(involute_points)
#
#
# if function == 'build_tooth':
#     tooth_num = 18
#     gear_params = get_gear_params(module=10, tooth_num=tooth_num)
#     # print_gear_params(*gear_params)
#     pitch_diameter, outside_diameter, root_diameter, base_diameter, addendum, dedendum = gear_params
#     inv_epitr_flat, angle = get_inv_epitr_flat(root_diameter, dedendum, STANDARD_PRESSURE_ANGLE)
#     involute_points = get_involute_points(base_diameter, inv_epitr_flat, pitch_diameter, outside_diameter)
#     points = build_tooth(root_diameter, involute_points, pitch_diameter, dedendum, inv_epitr_flat, base_diameter, tooth_num, outside_diameter)
#     points = populate_circ(*points, tooth_num)
#     simple_plot(*points, 'Involute')
#
#
# if function == 'get_epitrochoid_flat_point':
#     gear_params = get_gear_params(module=10, tooth_num=30)
#     # print_gear_params(*gear_params)
#     pitch_diameter, outside_diameter, root_diameter, base_diameter, addendum, dedendum = gear_params
#     inv_epitr_flat, angle = get_inv_epitr_flat(root_diameter, dedendum, STANDARD_PRESSURE_ANGLE)
#     print(get_epitrochoid_flat_point(pitch_diameter, dedendum, inv_epitr_flat))


if function == 'GearParams':
    module = 10
    tooth_num = 18
    params = GearParams(tooth_num=18, module=10, de_coef=1)
    params.diameters_to_radii()
    print(params)


if function == 'HalfTooth':
    tooth = HalfTooth(tooth_num=18, module=10, de_coef=1)
    hta = cartesian_to_polar(*tooth.half_tooth_profile)[0]
    # print(hta[-1] - hta[0])
    fta = cartesian_to_polar(*tooth.full_tooth_profile)[0]
    # print(fta[-1] - fta[0])
    # print(fta[0], fta[-1])
    # simple_plot(*tooth.half_tooth_profile, 'Half tooth profile')
    # simple_plot(*tooth.full_tooth_profile, 'Full tooth profile')

    sector_pts = tooth.get_sector_profile(np.pi * 0.5, np.pi + tooth.tooth_angle / 4, tooth.tooth_angle * 0.1)
    simple_plot(*sector_pts, 'Sector profile')
    # print(tooth)
    # points = tooth.get_gear_profile()
    # simple_plot(*points, 'Gear profile')
    # simple_plot(*tooth.half_tooth_profile, 'Half tooth profile', marker='o', markersize=1)



if function == 'equidistant':
    # equidistant(involute, 0, 2, 0.1, 0.1, r=2)
    # simple_plot(*equidistant(involute, 0, 2, 0.1, 0.0001, r=2), 'Involute', marker='x', markersize=3)
    simple_plot(*equidistant(epitrochoid_flat, 0, 2, 0.1, 0.1, R=4, l=1), 'Involute', marker='x', markersize=3)

#if function == '':








