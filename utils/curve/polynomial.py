# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.utils.geom import Spline
from sverchok.utils.polynomial import chebyshev_nodes, chebyshev_nodes_transform, polynomial_interpolate, chebyshev_T, legendre_P
from sverchok.utils.curve.core import SvTaylorCurve

def polynomial_interpolate_curve(basis, points, max_degree=None, tolerance=None, metric=None, tknots=None, use_chebyshev_nodes=False):
    if tknots is None:
        if metric is None:
            raise Exception("Either tknots or metric must be sppecified")
        if metric == 'CHEBYSHEV_NODES':
            tknots = chebyshev_nodes(len(points))
        else:
            tknots = Spline.create_knots(points, metric)
    if use_chebyshev_nodes:
        tknots = chebyshev_nodes_transform(tknots)
    print("T", tknots)
    t_min = tknots[0]
    t_max = tknots[-1]
    tknots = 2 * (tknots - t_min) / (t_max - t_min) - 1

    if basis == 'chebyshev_T':
        basis = chebyshev_T
    elif basis == 'legendre_P':
        basis = legendre_P
    else:
        raise ValueError(f"Unsupported basis: {basis}")

    polynomial = polynomial_interpolate(basis, tknots, points, max_degree=max_degree, tolerance=tolerance)
    polynomial = polynomial.linear_substitute(2, -1)
    return SvTaylorCurve.from_coefficients(polynomial.coeffs)

def legendre_interpolate_curve(points, max_degree=None, tolerance=None, metric=None, tknots=None):
    return polynomial_interpolate_curve('legendre_P', max_degree=max_degree, tolerance=tolerance, metric=metric, tknots=tknots)

def chebyshev_interpolate_curve(points, max_degree=None, tolerance=None, metric=None, tknots=None):
    return polynomial_interpolate_curve('chebyshev_T', max_degree=max_degree, tolerance=tolerance, metric=metric, tknots=tknots)

