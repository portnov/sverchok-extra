# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from sverchok.utils.geom import Spline, CubicSpline
from sverchok.utils.curve.splines import SvSplineCurve
from sverchok.utils.logging import getLogger

logger = getLogger()

def project(surface, derivs, uv_pts, vectors):
    #uv_pts = uv_pts[1:-1]
    u_tangents, v_tangents = derivs.unit_tangents()
    u_tangents = u_tangents[1:-1]
    v_tangents = v_tangents[1:-1]
    dus = (vectors * u_tangents).sum(axis=1)
    dvs = (vectors * v_tangents).sum(axis=1)
    #print(f"MU: {abs(dus).max()}, MV: {abs(dvs).max()}")
    dns = np.zeros_like(dus)
    uv_vectors = np.stack((dus, dvs, dns)).T
    uv_vectors = np.insert(uv_vectors, 0, [0,0,0], axis=0)
    uv_vectors = np.insert(uv_vectors, len(uv_vectors), [0,0,0], axis=0)
    #print(uv_vectors)
    #print(f"uv: {len(uv_pts)} + {len(uv_vectors)}")
    return uv_pts + uv_vectors
#    normals = derivs.unit_normals()[1:-1]
#    normal_coords = (vectors * normals).sum(axis=1)
#    return vectors - (normal_coords * normals)

def do_iteration(surface, uv_pts, prev_pts, step, tolerance=1e-3):
    #print(f"N: {len(uv_pts)}")
    data = surface.derivatives_data_array(uv_pts[:,0], uv_pts[:,1])
    pts = data.points

    if prev_pts is not None:
        diff = (prev_pts - pts).max()
        if diff < tolerance:
            return None
        
    dvs = pts[1:] - pts[:-1]
    sums = dvs[1:] - dvs[:-1]
    #print(f"{len(pts)} => {len(sums)}")
    sums *= step
    uv_pts = project(surface, data, uv_pts, sums)
    return pts, uv_pts

def process(surface, pt1, pt2, n_segments, n_iterations, step, tolerance):
    uv_pts = np.linspace(pt1, pt2, num=n_segments)
    prev_pts = None
    for i in range(n_iterations):
        r = do_iteration(surface, uv_pts, prev_pts, step, tolerance)
        if r is not None:
            prev_pts, uv_pts = r
        else:
            logger.info(f"Stop at {i}'th iteration")
            break
    return uv_pts

def mk_curve(surface, uv_pts):
    pts = surface.evaluate_array(uv_pts[:,0], uv_pts[:,1])
    tknots = Spline.create_knots(pts)
    spline = CubicSpline(uv_pts, tknots=tknots)
    return SvSplineCurve(spline)

def calculate_geodesic_curve(surface, point1, point2, n_points, iterations, step, tolerance):
    uv_pts = process(surface, point1, point2, n_points, iterations, step, tolerance)
    curve = mk_curve(surface, uv_pts)
    return uv_pts.tolist(), curve

