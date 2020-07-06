
import numpy as np
from math import sqrt, atanh, sinh, cosh

from mathutils import kdtree
from mathutils.bvhtree import BVHTree

from sverchok.utils.curve import SvCurve, SvIsoUvCurve
from sverchok.utils.logging import debug, info
from sverchok.utils.geom import PlaneEquation, LineEquation

from sverchok.dependencies import scipy, skimage
from sverchok.utils.marching_squares import make_contours

if scipy is not None:
    from scipy.optimize import root_scalar, root

if skimage is not None:
    from skimage import measure

def intersect_surface_plane_msquares(surface, plane, need_points = True, samples_u=50, samples_v=50):
    u_min, u_max = surface.get_u_min(), surface.get_u_max()
    v_min, v_max = surface.get_v_min(), surface.get_v_max()
    u_range = np.linspace(u_min, u_max, num=samples_u)
    v_range = np.linspace(v_min, v_max, num=samples_v)
    us, vs = np.meshgrid(u_range, v_range, indexing='ij')
    us, vs = us.flatten(), vs.flatten()

    surface_points = surface.evaluate_array(us, vs)
    normal = np.array(plane.normal)
    p2 = np.apply_along_axis(lambda p : normal.dot(p), 1, surface_points)
    data = p2 + plane.d
    data = data.reshape((samples_u, samples_v))

    contours = measure.find_contours(data, level=0.0)

    u_size = (u_max - u_min) / samples_u
    v_size = (v_max - v_min) / samples_v

    uv_points, _, _ = make_contours(samples_u, samples_v,
                    u_min, u_size, v_min, v_size,
                    0,
                    contours,
                    make_faces = False,
                    connect_bounds = False)

    if need_points:
        points = []
        for uv_i in uv_points:
            us_i = [p[0] for p in uv_i]
            vs_i = [p[1] for p in uv_i]
            ps = surface.evaluate_array(np.array(us_i), np.array(vs_i)).tolist()
            points.append(ps)
    else:
        points = []

    return uv_points, points

def intersect_surface_plane_uv(surface, plane, samples_u = 50, samples_v = 50, init_samples=10, ortho_samples=10, tolerance=1e-3, maxiter=50):
    # Unsorted!
    u_min, u_max = surface.get_u_min(), surface.get_u_max()
    v_min, v_max = surface.get_v_min(), surface.get_v_max()
    u_range = np.linspace(u_min, u_max, num=samples_u)
    v_range = np.linspace(v_min, v_max, num=samples_v)

    points = []
    for u in u_range:
        curve = SvIsoUvCurve(surface, 'U', u)
        ps = intersect_curve_plane(curve, plane,
                    init_samples=init_samples, ortho_samples=ortho_samples,
                    tolerance=tolerance, maxiter=maxiter)
        points.extend(ps)
    for v in v_range:
        curve = SvIsoUvCurve(surface, 'V', v)
        ps = intersect_curve_plane(curve, plane,
                    init_samples=init_samples, ortho_samples=ortho_samples,
                    tolerance=tolerance, maxiter=maxiter)
        points.extend(ps)
    return [tuple(p) for p in points]

