
import numpy as np
from math import sqrt, atanh, sinh, cosh

from mathutils import kdtree

from sverchok.utils.curve import SvCurve, SvIsoUvCurve
from sverchok_extra.dependencies import scipy

if scipy is not None:
    from scipy.optimize import root_scalar

class ProjectionResult(object):
    def __init__(self, us, points, source):
        self.us = us
        self.points = points
        self.source = source

        self.kdt = kdt = kdtree.KDTree(len(points))
        for i, v in enumerate(points):
            kdt.insert(v, i)
        kdt.balance()

        nearest, i, distance = kdt.find(source)
        self.nearest = np.array(nearest)
        self.nearest_idx = i
        self.nearest_distance = distance
        self.nearest_u = us[i]

def ortho_project_curve(src_point, curve, init_samples=10):
    def goal(t):
        point_on_curve = curve.evaluate(t)
        dv = src_point - point_on_curve
        tangent = curve.tangent(t)
        return dv.dot(tangent)

    u_min, u_max = curve.get_u_bounds()
    u_samples = np.linspace(u_min, u_max, num=init_samples)

    u_ranges = []
    prev_value = goal(u_min)
    prev_u = u_min
    for u in u_samples[1:]:
        value = goal(u)
        if value * prev_value < 0:
            u_ranges.append((prev_u, u))
        prev_u = u
        prev_value = value

    points = []
    us = []
    for u1, u2 in u_ranges:
        u0 = (u1 + u2) / 2.0
        result = root_scalar(goal, method='ridder',
                        bracket = (u1, u2),
                        x0 = u0)
        u = result.root
        us.append(u)
        point = curve.evaluate(u)
        points.append(point)

    if not us:
        raise Exception("Can't calculate the projection of {} onto {}".format(src_point, curve))
    result = ProjectionResult(us, points, src_point)
    return result

def ortho_project_surface(src_point, surface, init_samples=10, maxiter=30, tolerance=1e-4):
    u_min, u_max = surface.get_u_min(), surface.get_u_max()
    v_min, v_max = surface.get_v_min(), surface.get_v_max()

    u0 = (u_min + u_max) / 2.0
    v0 = (v_min + v_max) / 2.0

    fixed_axis = 'U'
    fixed_axis_value = u0
    prev_fixed_axis_value = v0
    prev_point = surface.evaluate(u0, v0)

    i = 0
    while True:
        if i > maxiter:
            raise Exception("No convergence")
        curve = SvIsoUvCurve(surface, fixed_axis, fixed_axis_value)
        projection = ortho_project_curve(src_point, curve, init_samples)
        point = projection.nearest
        dv = point - prev_point
        if np.linalg.norm(dv) < tolerance:
            break
        fixed_axis_value = projection.nearest_u
        if fixed_axis == 'U':
            fixed_axis = 'V'
        else:
            fixed_axis = 'U'
        prev_fixed_axis_value = fixed_axis_value
        prev_point = point
        i += 1

    if fixed_axis == 'U':
        u, v = prev_fixed_axis_value, fixed_axis_value
    else:
        u, v = fixed_axis_value, prev_fixed_axis_value

    return u, v, point

