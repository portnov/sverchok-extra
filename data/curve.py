
import numpy as np
from math import sin, cos, pi
from mathutils import Matrix, Vector
from mathutils import noise
from mathutils import kdtree
from mathutils import bvhtree

from sverchok.utils.geom import PlaneEquation, LineEquation
from sverchok_extra.utils.integrate import TrapezoidIntegral

##################
#                #
#  Curves        #
#                #
##################

def make_euclidian_ts(pts):
    tmp = np.linalg.norm(pts[:-1] - pts[1:], axis=1)
    tknots = np.insert(tmp, 0, 0).cumsum()
    tknots = tknots / tknots[-1]
    return tknots

class SvExCurve(object):
    def evaluate(self, t):
        raise Exception("not implemented!")

    def evaluate_array(self, ts):
        raise Exception("not implemented!")

    def tangent(self, t):
        v = self.evaluate(t)
        h = self.tangent_delta
        v_h = self.evaluate(t+h)
        return (v_h - v) / h

    def tangent_array(self, ts):
        vs = self.evaluate_array(ts)
        h = self.tangent_delta
        u_max = self.curve.get_u_bounds()[1]
        bad_idxs = (ts+h) > u_max
        good_idxs = (ts+h) <= u_max
        ts_h = ts + h
        ts_h[bad_idxs] = (ts - h)[bad_idxs]

        vs_h = self.evaluate_array(ts_h)
        tangents_plus = (vs_h - vs) / h
        tangents_minus = (vs - vs_h) / h
        tangents_x = np.where(good_idxs, tangents_plus[:,0], tangents_minus[:,0])
        tangents_y = np.where(good_idxs, tangents_plus[:,1], tangents_minus[:,1])
        tangents_z = np.where(good_idxs, tangents_plus[:,2], tangents_minus[:,2])
        tangents = np.stack((tangents_x, tangents_y, tangents_z)).T
        return tangents

    def second_derivative(self, t):
        if hasattr(self, 'tangent_delta'):
            h = self.tangent_delta
        else:
            h = 0.001
        v0 = self.evaluate(t-h)
        v1 = self.evaluate(t)
        v2 = self.evaluate(t+h)
        return (v2 - 2*v1 + v0) / (h * h)

    def second_derivative_array(self, ts):
        h = 0.001
        v0s = self.evaluate_array(ts-h)
        v1s = self.evaluate_array(ts)
        v2s = self.evaluate_array(ts+h)
        return (v2s - 2*v1s + v0s) / (h * h)

    def third_derivative_array(self, ts):
        h = 0.001
        v0s = self.evaluate_array(ts)
        v1s = self.evaluate_array(ts+h)
        v2s = self.evaluate_array(ts+2*h)
        v3s = self.evaluate_array(ts+3*h)
        return (- v0s + 3*v1s - 3*v2s + v3s) / (h * h * h)

    def derivatives_array(self, n, ts):
        result = []
        if n >= 1:
            first = self.tangent_array(ts)
            result.append(first)

        h = 0.001
        if n >= 2:
            minus_h = self.evaluate_array(ts-h)
            points = self.evaluate_array(ts)
            plus_h = self.evaluate_array(ts+h)
            second = (plus_h - 2*points + minus_h) / (h * h)
            result.append(second)

        if n >= 3:
            v0s = points
            v1s = plus_h
            v2s = self.evaluate_array(ts+2*h)
            v3s = self.evaluate_array(ts+3*h)
            third = (- v0s + 3*v1s - 3*v2s + v3s) / (h * h * h)
            result.append(third)

        return result

    def main_normal(self, t, normalize=True):
        tangent = self.tangent(t)
        binormal = self.binormal(t, normalize)
        v = np.cross(binormal, tangent)
        if normalize:
            v = v / np.linalg.norm(v)
        return v

    def binormal(self, t, normalize=True):
        tangent = self.tangent(t)
        second = self.second_derivative(t)
        v = np.cross(tangent, second)
        if normalize:
            v = v / np.linalg.norm(v)
        return v

    def main_normal_array(self, ts, normalize=True):
        tangents = self.tangent_array(ts)
        binormals = self.binormal_array(ts, normalize)
        v = np.cross(binormals, tangents)
        if normalize:
            norms = np.linalg.norm(v, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            v[nonzero] = v[nonzero] / norms[nonzero][:,0][np.newaxis].T
        return v

    def binormal_array(self, ts, normalize=True):
        tangents, seconds = self.derivatives_array(2, ts)
        v = np.cross(tangents, seconds)
        if normalize:
            norms = np.linalg.norm(v, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            v[nonzero] = v[nonzero] / norms[nonzero][:,0][np.newaxis].T
        return v

    def tangent_normal_binormal_array(self, ts, normalize=True):
        tangents, seconds = self.derivatives_array(2, ts)
        binormals = np.cross(tangents, seconds)
        if normalize:
            norms = np.linalg.norm(binormals, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            binormals[nonzero] = binormals[nonzero] / norms[nonzero][:,0][np.newaxis].T
        normals = np.cross(binormals, tangents)
        if normalize:
            norms = np.linalg.norm(normals, axis=1, keepdims=True)
            nonzero = (norms > 0)[:,0]
            normals[nonzero] = normals[nonzero] / norms[nonzero][:,0][np.newaxis].T
        return tangents, normals, binormals

    def frame_array(self, ts):
        tangents, normals, binormals = self.tangent_normal_binormal_array(ts)
        tangents = tangents / np.linalg.norm(tangents, axis=1)[np.newaxis].T
        matrices_np = np.dstack((normals, binormals, tangents))
        matrices_np = np.transpose(matrices_np, axes=(0,2,1))
        matrices_np = np.linalg.inv(matrices_np)
        return matrices_np, normals, binormals

    def curvature_array(self, ts):
        tangents, seconds = self.derivatives_array(2, ts)
        numerator = np.linalg.norm(np.cross(tangents, seconds), axis=1)
        tangents_norm = np.linalg.norm(tangents, axis=1)
        denominator = tangents_norm * tangents_norm * tangents_norm
        return numerator / denominator

    def torsion_array(self, ts):
        tangents, seconds, thirds = self.derivatives_array(3, ts)
        seconds_thirds = np.cross(seconds, thirds)
        numerator = (tangents * seconds_thirds).sum(axis=1)
        #numerator = np.apply_along_axis(lambda tangent: tangent.dot(seconds_thirds), 1, tangents)
        first_second = np.cross(tangents, seconds)
        denominator = np.linalg.norm(first_second, axis=1)
        return numerator / (denominator * denominator)

    def pre_calc_torsion_integral(self, resolution):
        t_min, t_max = self.get_u_bounds()
        ts = np.linspace(t_min, t_max, resolution)
        vectors = self.evaluate_array(ts)
        dvs = vectors[1:] - vectors[:-1]
        lengths = np.linalg.norm(dvs, axis=1)
        xs = np.insert(np.cumsum(lengths), 0, 0)
        ys = self.torsion_array(ts)
        self._torsion_integral = TrapezoidIntegral(ts, xs, ys)
        self._torsion_integral.calc()

    def torsion_integral(self, ts):
        return self._torsion_integral.evaluate_cubic(ts)

    def get_u_bounds(self):
        raise Exception("not implemented!")

class SvExLine(SvExCurve):
    def __init__(self, point, direction):
        self.point = point
        self.direction = np.array(direction)
        self.u_bounds = (0.0, 1.0)

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        return self.point + t * self.direction

    def evaluate_array(self, ts):
        ts = ts[np.newaxis].T
        return self.point + ts * self.direction

    def tangent(self, t):
        tg = self.direction
        n = np.linalg.norm(tg)
        return tg / n

    def tangent_array(self, ts):
        tg = self.direction
        n = np.linalg.norm(tg)
        tangent = tg / n
        return np.tile(tangent, len(ts))

class SvExCircle(SvExCurve):
    def __init__(self, matrix, radius):
        self.matrix = np.array(matrix.to_3x3())
        self.center = np.array(matrix.translation)
        self.radius = radius
        self.u_bounds = (0.0, 2*pi)

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        r = self.radius
        x = r * cos(t)
        y = r * sin(t)
        return self.matrix @ np.array([x, y, 0]) + self.center

    def evaluate_array(self, ts):
        r = self.radius
        xs = r * np.cos(ts)
        ys = r * np.sin(ts)
        zs = np.zeros_like(xs)
        vertices = np.stack((xs, ys, zs)).T
        return np.apply_along_axis(lambda v: self.matrix @ v, 1, vertices) + self.center

    def tangent(self, t):
        x = - self.radius * sin(t)
        y = self.radius * cos(t)
        z = 0
        return self.matrix @ np.array([x, y, z])

    def tangent_array(self, ts):
        xs = - self.radius * np.sin(ts)
        ys = self.radius * np.cos(ts)
        zs = np.zeros_like(xs)
        vectors = np.stack((xs, ys, zs)).T
        return np.apply_along_axis(lambda v: self.matrix @ v, 1, vectors)

#     def second_derivative_array(self, ts):
#         xs = - np.cos(ts)
#         ys = - np.sin(ts)
#         zs = np.zeros_like(xs)
#         vectors = np.stack((xs, ys, zs)).T
#         return np.apply_along_axis(lambda v: self.matrix @ v, 1, vectors)

class SvExLambdaCurve(SvExCurve):
    def __init__(self, function):
        self.function = function
        self.u_bounds = (0.0, 1.0)
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        return self.function(t)

    def evaluate_array(self, ts):
        return np.vectorize(self.function, signature='()->(3)')(ts)

    def tangent(self, t):
        point = self.function(t)
        point_h = self.function(t+self.tangent_delta)
        return (point_h - point) / self.tangent_delta

    def tangent_array(self, ts):
        points = np.vectorize(self.function, signature='()->(3)')(ts)
        points_h = np.vectorize(self.function, signature='()->(3)')(ts+self.tangent_delta)
        return (points_h - points) / self.tangent_delta

class SvExGeomdlCurve(SvExCurve):
    def __init__(self, curve):
        self.curve = curve
        self.u_bounds = (0.0, 1.0)

    def evaluate(self, t):
        v = self.curve.evaluate_single(t)
        return np.array(v)

    def evaluate_array(self, ts):
        t_min, t_max = self.get_u_bounds()
        ts[ts < t_min] = t_min
        ts[ts > t_max] = t_max
        vs = self.curve.evaluate_list(list(ts))
        return np.array(vs)

    def tangent(self, t):
        v = self.curve.tangent(t, normalize=False)
        return np.array(v)

    def tangent_array(self, ts):
        t_min, t_max = self.get_u_bounds()
        ts[ts < t_min] = t_min
        ts[ts > t_max] = t_max
        vs = self.curve.tangent(list(ts), normalize=False)
        return np.array([t[1] for t in vs])

    def second_derivative(self, t):
        p, first, second = self.curve.derivatives(t, order=2)
        return np.array(second)

    def second_derivative_array(self, ts):
        return np.vectorize(self.second_derivative, signature='()->(3)')(ts)

    def third_derivative(self, t):
        p, first, second, third = self.curve.derivatives(t, order=3)
        return np.array(third)

    def third_derivative_array(self, ts):
        return np.vectorize(self.third_derivative, signature='()->(3)')(ts)

    def derivatives_array(self, n, ts):
        def derivatives(t):
            result = self.curve.derivatives(t, order=n)
            return np.array(result[1:])
        result = np.vectorize(derivatives, signature='()->(n,3)')(ts)
        result = np.transpose(result, axes=(1, 0, 2))
        return result

    def get_u_bounds(self):
        return self.u_bounds

class SvExSplineCurve(SvExCurve):
    def __init__(self, spline):
        self.spline = spline

    def evaluate(self, t):
        v = self.spline.eval_at_point(t)
        return np.array(v)

    def evaluate_array(self, ts):
        vs = self.spline.eval(ts)
        return np.array(vs)

    def tangent(self, t):
        vs = self.spline.tangent(np.array([t]))
        return vs[0]

    def tangent_array(self, ts):
        return self.spline.tangent(ts)

    def get_u_bounds(self):
        return (0.0, 1.0)

class SvExRbfCurve(SvExCurve):
    def __init__(self, rbf, u_bounds):
        self.rbf = rbf
        self.u_bounds = u_bounds
        self.tangent_delta = 0.0001

    def get_u_bounds(self):
        return self.u_bounds

    def evaluate(self, t):
        v = self.rbf(t)
        return v

    def evaluate_array(self, ts):
        vs = self.rbf(ts)
        return vs

    def tangent(self, t):
        point = self.rbf(t)
        point_h = self.rbf(t+self.tangent_delta)
        return (point_h - point) / self.tangent_delta
    
    def tangent_array(self, ts):
        points = self.rbf(ts)
        points_h = self.rbf(ts+self.tangent_delta)
        return (points_h - points) / self.tangent_delta

class SvExDeformedByFieldCurve(SvExCurve):
    def __init__(self, curve, field, coefficient=1.0):
        self.curve = curve
        self.field = field
        self.coefficient = coefficient
        self.tangent_delta = 0.001

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

    def evaluate(self, t):
        v = self.curve.evaluate(t)
        vec = self.field.evaluate(*tuple(v))
        return v + self.coefficient * vec

    def evaluate_array(self, ts):
        vs = self.curve.evaluate_array(ts)
        xs, ys, zs = vs[:,0], vs[:,1], vs[:,2]
        vxs, vys, vzs = self.field.evaluate_grid(xs, ys, zs)
        vecs = np.stack((vxs, vys, vzs)).T
        return vs + self.coefficient * vecs

class SvExCastCurveToPlane(SvExCurve):
    def __init__(self, curve, point, normal, coefficient):
        self.curve = curve
        self.point = point
        self.normal = normal
        self.coefficient = coefficient
        self.plane = PlaneEquation.from_normal_and_point(normal, point)
        self.tangent_delta = 0.001

    def evaluate(self, t):
        point = self.curve.evaluate(t)
        target = np.array(self.plane.projection_of_point(point))
        k = self.coefficient
        return (1 - k) * point + k * target

    def evaluate_array(self, ts):
        points = self.curve.evaluate_array(ts)
        targets = self.plane.projection_of_points(points)
        k = self.coefficient
        return (1 - k) * points + k * targets

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

class SvExCastCurveToSphere(SvExCurve):
    def __init__(self, curve, center, radius, coefficient):
        self.curve = curve
        self.center = center
        self.radius = radius
        self.coefficient = coefficient
        self.tangent_delta = 0.001

    def evaluate(self, t):
        return self.evaluate_array(np.array([t]))[0]

    def evaluate_array(self, ts):
        points = self.curve.evaluate_array(ts)
        points = points - self.center
        norms = np.linalg.norm(points, axis=1)[np.newaxis].T
        normalized = points / norms
        targets = self.radius * normalized + self.center
        k = self.coefficient
        return (1 - k) * points + k * targets

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

class SvExCastCurveToCylinder(SvExCurve):
    def __init__(self, curve, center, direction, radius, coefficient):
        self.curve = curve
        self.center = center
        self.direction = direction
        self.radius = radius
        self.coefficient = coefficient
        self.line = LineEquation.from_direction_and_point(direction, center)
        self.tangent_delta = 0.001

    def evaluate(self, t):
        point = self.curve.evaluate(t)
        projection_to_line = self.line.projection_of_point(point)
        projection_to_line = np.array(projection_to_line)
        radial = point - projection_to_line
        radius = self.radius * radial / np.linalg.norm(radial)
        projection = projection_to_line + radius
        k = self.coefficient
        return (1 - k) * point + k * projection
    
    def evaluate_array(self, ts):
        points = self.curve.evaluate_array(ts)
        projection_to_line = self.line.projection_of_points(points)
        radial = points - projection_to_line
        radius = self.radius * radial / np.linalg.norm(radial, axis=1, keepdims=True)
        projections = projection_to_line + radius
        k = self.coefficient
        return (1 - k) * points + k * projections

    def get_u_bounds(self):
        return self.curve.get_u_bounds()

def register():
    pass

def unregister():
    pass


