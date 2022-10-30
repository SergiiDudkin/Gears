import numpy as np
from transforms import make_angrad_func, mirror
from curves import circle, involute, epitrochoid, epitrochoid_flat


def get_inv_epitr_flat(root_diameter, dedendum, pressure_angle):
    root_radius = root_diameter / 2
    inv_epitr_flat = np.sqrt((dedendum / np.tan(pressure_angle)) ** 2 + root_radius ** 2)
    angle = np.pi / 2 - np.arccos(root_radius / inv_epitr_flat) + pressure_angle
    return inv_epitr_flat, angle


def get_inv_epitr(pitch_diameter, pitch_diameter2, dedendum, pressure_angle):  # !!! Check angle
    # Solve the first triangle using law of sines
    b = pitch_diameter2 / 2  # 2nd gear pitch radius
    a = b + dedendum
    alpha = np.pi / 2 + pressure_angle
    R2t = a / np.sin(alpha)
    beta = np.arcsin(b / R2t)  # Angle beta is guarantied to be acute
    gamma = np.pi - alpha - beta
    c = R2t * np.sin(gamma)

    # Solve the first triangle using law of cosines
    c_ = c
    b_ = pitch_diameter / 2  # Pitch radius
    alpha_ = np.pi / 2 - pressure_angle
    a_ = np.sqrt(b_ ** 2 + c_ ** 2 - 2 * b_ * c_ * np.cos(alpha_))

    # Find angle using law of cosines
    beta_ = np.arccos((a_ ** 2 + c_ ** 2 - b_ ** 2) / (2 * a_ * c_))
    angle = beta + beta_

    return a_, angle


def get_involute_points(base_diameter, inv_epitr, pitch_diameter, outside_diameter):
    involute_angrad = make_angrad_func(involute)
    base_radius = base_diameter / 2
    pitch_radius = pitch_diameter / 2
    outside_radius = outside_diameter / 2
    return [involute_angrad(rad, 0, 2, base_radius) for rad in (inv_epitr, pitch_radius, outside_radius)]


def get_epitrochoid_flat_point(pitch_diameter, dedendum, inv_epitr_flat):
    epitrochoid_flat_angrad = make_angrad_func(epitrochoid_flat)
    pitch_radius = pitch_diameter / 2
    return epitrochoid_flat_angrad(inv_epitr_flat, 0, 2, pitch_radius, dedendum)


def get_epitrochoid_point(pitch_diameter, pitch_diameter2, dedendum, inv_epitr):
    epitrochoid_angrad = make_angrad_func(epitrochoid)
    pitch_radius = pitch_diameter / 2
    pitch_radius2 = pitch_diameter2 / 2
    return epitrochoid_angrad(inv_epitr, 0, 2, pitch_radius, pitch_radius2, pitch_radius2 + dedendum)


def build_tooth(root_diameter, involute_points, pitch_diameter, dedendum, inv_epitr_flat, base_diameter, tooth_num, outside_diameter):
    root_radius = root_diameter / 2
    pitch_radius = pitch_diameter / 2
    base_radius = base_diameter / 2
    outside_radius = outside_diameter / 2
    quater_angle = np.pi / 2 / tooth_num

    # Get points of involute
    ang_inv_epitr = involute_points[0][0]
    t_inv_epitr = involute_points[0][3]
    ang_pitch = involute_points[1][0]
    t_outside = involute_points[2][3]
    ang_outside = involute_points[2][0]
    t_s = np.arange(t_inv_epitr, t_outside, 0.01)
    points_involute = involute(t_s, base_radius, a0=-ang_pitch)

    # Get points of epitrochoid flat
    ang_epitr_inv, x, y, t_epitr_inv = get_epitrochoid_flat_point(pitch_diameter, dedendum, inv_epitr_flat)
    rot_ang = ang_epitr_inv + ang_inv_epitr - ang_pitch
    t_s = np.arange(0, -t_epitr_inv, -0.005)
    points_epitrochoid_flat = epitrochoid_flat(t_s, pitch_radius, dedendum, a0=rot_ang)

    # Get points of outside circle
    t_s = np.arange(ang_outside, quater_angle, 0.0005)
    points_outside = circle(t_s, outside_radius, a0=0)

    # Get points of root circle
    t_s = np.arange(-quater_angle, rot_ang, 0.0005)
    points_root = circle(t_s, root_radius, a0=0)

    points_combined = np.hstack((points_root, points_epitrochoid_flat, points_involute, points_outside))
    # print(points_combined.shape)
    # print(type(points_combined))
    # a = np.arange(10).reshape(2, 5)
    # print(a.shape)
    # print(type(a))
    # print(a[:, 0])

    seg_st = np.array([0, 0])
    # b = np.array(points_root)
    seg_en = np.array(points_root)[:, 0]
    print(seg_en)
    reflected = np.transpose([mirror(point, seg_st, seg_en) for point in np.transpose(points_combined)])

    # return points_combined
    return np.hstack((reflected[:, ::-1], points_combined))
