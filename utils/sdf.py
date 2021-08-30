
import numpy as np

from sverchok_extra.dependencies import sdf
if sdf is not None:
    from sdf import *

from sverchok.utils.field.scalar import SvScalarField

class SvExSdfScalarField(SvScalarField):
    def __init__(self, sdf):
        self.sdf = sdf

    def evaluate_grid(self, xs, ys, zs):
        points = np.stack((xs, ys, zs)).T
        r = self.sdf.f(points)
        return r

    def evaluate(self, x, y, z):
        points = np.array([[x,y,z]])
        r = self.sdf.f(points)
        return r

def scalar_field_to_sdf(field, iso_value):
    def function():
        def evaluate_array(points):
            xs = points[:,0]
            ys = points[:,1]
            zs = points[:,2]
            return field.evaluate_grid(xs, ys, zs) - iso_value
        return evaluate_array

    return sdf3(function)()

def cartesian_product(*arrays):
    la = len(arrays)
    dtype = np.result_type(*arrays)
    arr = np.empty([len(a) for a in arrays] + [la], dtype=dtype)
    for i, a in enumerate(np.ix_(*arrays)):
        arr[...,i] = a
    return arr.reshape(-1, la)

def estimate_bounds(field):
    # TODO: raise exception if bound estimation fails
    s = 16
    x0 = y0 = z0 = -1e9
    x1 = y1 = z1 = 1e9
    prev = None
    for i in range(32):
        X = np.linspace(x0, x1, s)
        Y = np.linspace(y0, y1, s)
        Z = np.linspace(z0, z1, s)
        d = np.array([X[1] - X[0], Y[1] - Y[0], Z[1] - Z[0]])
        threshold = np.linalg.norm(d) / 2
        if threshold == prev:
            break
        prev = threshold
        pts = cartesian_product(X, Y, Z)
        xs = pts[:,0]
        ys = pts[:,1]
        zs = pts[:,2]
        volume = field.evaluate_grid(xs,ys,zs)
        volume = volume.reshape((len(X), len(Y), len(Z)))
        where = np.argwhere(np.abs(volume) <= threshold)
        x1, y1, z1 = (x0, y0, z0) + where.max(axis=0) * d + d / 2
        x0, y0, z0 = (x0, y0, z0) + where.min(axis=0) * d - d / 2
    return ((x0, y0, z0), (x1, y1, z1))

easing_dict = dict(enumerate([
        ease.linear,
        ease.in_quad, ease.out_quad, ease.in_out_quad,
        ease.in_cubic, ease.out_cubic, ease.in_out_cubic,
        ease.in_quart, ease.out_quart, ease.in_out_quart,
        ease.in_quint, ease.out_quint, ease.in_out_quint,
        ease.in_sine, ease.out_sine, ease.in_out_sine,
        ease.in_expo, ease.out_expo, ease.in_out_expo,
        ease.in_circ, ease.out_circ, ease.in_out_circ,
        ease.in_elastic, ease.out_elastic, ease.in_out_elastic,
        ease.in_back, ease.out_back, ease.in_out_back,
        ease.in_bounce, ease.out_bounce, ease.in_out_bounce,
        ease.in_square, ease.out_square, ease.in_out_square
    ]))

