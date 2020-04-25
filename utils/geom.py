
import numpy as np
from math import sqrt, atanh, sinh, cosh

from mathutils import kdtree
from mathutils.bvhtree import BVHTree

from sverchok.utils.curve import SvCurve, SvIsoUvCurve
from sverchok_extra.dependencies import scipy

if scipy is not None:
    from scipy.optimize import root_scalar, root

class CurveProjectionResult(object):
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
    result = CurveProjectionResult(us, points, src_point)
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

class RaycastResult(object):
    def __init__(self):
        self.init_us = None
        self.init_vs = None
        self.init_ts = None
        self.init_points = None
        self.points = []
        self.uvs = []
        self.us = []
        self.vs = []

def raycast_surface(surface, src_points, directions, samples=50, precise=True, calc_points=True, method='hybr'):
    def make_faces():
        faces = []
        for row in range(samples - 1):
            for col in range(samples - 1):
                i = row * samples + col
                face = (i, i+samples, i+samples+1, i+1)
                faces.append(face)
        return faces

    def init_guess():
        u_min = surface.get_u_min()
        u_max = surface.get_u_max()
        v_min = surface.get_v_min()
        v_max = surface.get_v_max()
        us = np.linspace(u_min, u_max, num=samples)
        vs = np.linspace(v_min, v_max, num=samples)
        us, vs = np.meshgrid(us, vs)
        us = us.flatten()
        vs = vs.flatten()

        points = surface.evaluate_array(us, vs).tolist()
        faces = make_faces()

        bvh = BVHTree.FromPolygons(points, faces)

        us_out = []
        vs_out = []
        t_out = []
        nearest_out = []
        h2 = (u_max - u_min) / (2 * samples)
        for src_point, direction in zip(src_points, directions):
            nearest, normal, index, distance = bvh.ray_cast(src_point, direction)
            us_out.append(us[index] + h2)
            vs_out.append(vs[index] + h2)
            t_out.append(distance)
            nearest_out.append(tuple(nearest))

        return us_out, vs_out, t_out, nearest_out

    def goal(surface, src_point, direction):
        def function(p):
            on_surface = surface.evaluate(p[0], p[1])
            on_line = src_point + direction * p[2]
            return (on_surface - on_line).flatten()
        return function

    result = RaycastResult()
    result.init_us, result.init_vs, result.init_ts, result.init_points = init_guess()
    for point, direction, init_u, init_v, init_t, init_point in zip(src_points, directions, result.init_us, result.init_vs, result.init_ts, result.init_points):
        if precise:
            direction = np.array(direction)
            direction = direction / np.linalg.norm(direction)
            projection = root(goal(surface, np.array(point), direction),
                        x0 = np.array([init_u, init_v, init_t]),
                        method = method)
            if not projection.success:
                raise Exception("Can't find the projection for {}: {}".format(point, projection.message))
            u0, v0, t0 = projection.x
        else:
            u0, v0 = init_u, init_v
            result.points.append(init_point)

        result.uvs.append((u0, v0, 0))
        result.us.append(u0)
        result.vs.append(v0)

    if precise and calc_points:
        result.points = surface.evaluate_array(np.array(result.us), np.array(result.vs)).tolist()

    return result

