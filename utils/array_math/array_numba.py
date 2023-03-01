# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import logging
from functools import wraps

import numpy as np

try:
    import awkward as ak
    import numba
except ImportError:
    ak = None
    numba = None


logger = logging.getLogger('sverchok')


def add_numba_implementation(decorated_func):
    if numba is not None:
        implementation_name = decorated_func.__name__
        try:
            implementation = globals()[implementation_name]
        except KeyError:
            implementation = decorated_func
            logger.error(f'Function "{implementation_name}" is not found')
    else:
        implementation = decorated_func

    @wraps(implementation)
    def wrap(*args, **kwargs):
        return implementation(*args, **kwargs)

    return wrap


def subdivide_polyline(verts, cuts, interpolation='LINEAR'):
    verts = ak.from_regular(verts)  # https://github.com/scikit-hep/awkward/discussions/2197
    segment_shape = ak.num(verts, axis=-1)[..., :-1]
    _, cuts2 = ak.broadcast_arrays(segment_shape, cuts)  # [[2, 3], [4]]
    flat_result, flat_count = _subdivide_polylines(verts, cuts2)
    return ak.unflatten(flat_result, flat_count, axis=0)


def connect_polyline(verts):
    flat_result, flat_count = _connect_polyline(verts)
    if flat_count is not None:
        return ak.unflatten(flat_result, flat_count, axis=0)
    else:
        return flat_result


if numba is not None:

    @numba.njit
    def _subdivide_polylines(polylines, cuts):
        # if interpolation == 'LINEAR':
        #     interpolation_func = _linear_interpolation
        # elif interpolation == 'CUBIC':
        #     interpolation_func = _cubic_interpolation
        # elif interpolation == 'CATMULL_ROM':
        #     interpolation = _catmull_rom_interpolation
        # else:
        #     raise TypeError("Given interpolation type is unknown.")

        # Pre-pass over the data to determine how large our arrays need to be
        final_vertex_count = 0
        for line_cuts in cuts:
            for cut in line_cuts:
                final_vertex_count += cut  # etra points inside segment
                final_vertex_count += 1  # first point of each segment
            final_vertex_count += 1  # last point of last segment

        flat_result = np.empty((final_vertex_count, 3), dtype=np.float64)
        flat_result = np.empty((10, 3), dtype=np.float64)
        flat_count = np.zeros(len(polylines), dtype=np.int64)
        flat_count = np.zeros(10, dtype=np.int64)

        # Keep track of the vertex index in the flat result
        l_vertex_index = 0

        # For each polyline
        for i_line, line in enumerate(polylines):
            assert len(line) >= 2

            # Add first point of the line
            start = np.asarray(line[0])
            flat_result[l_vertex_index] = start
            l_vertex_index += 1

            # For each segment (three vertices = two segments)
            segments_num = len(line) - 1
            for j_segment in range(segments_num):
                seg_cuts = cuts[i_line][j_segment]
                _subdivide_segment(
                    line, j_segment, seg_cuts, flat_result[l_vertex_index:])
                l_vertex_index += seg_cuts+1

            flat_count[i_line] = len(line) + sum([n for n in cuts[i_line]])

        return flat_result, flat_count


    @numba.njit
    def _subdivide_segment(polyline, segment_index, cuts, result):
        start = np.asarray(polyline[segment_index])
        stop = np.asarray(polyline[segment_index + 1])
        for i, k_segment_vertex in enumerate(range(1, cuts + 2)):
            # Interpolate between start and stop
            t = k_segment_vertex / (cuts + 1)
            result[i] = _linear_interpolation(start, stop, t)


    @numba.njit
    def _linear_interpolation(val1, val2, factor):
        return val1 * (1 - factor) + val2 * factor


    @numba.njit
    def _cubic_interpolation(v0, v1, v2, v3, factor):
        f2 = factor ** 2
        a0 = v3 - v2 - v0 + v1
        a1 = v0 - v1 - a0
        a2 = v2 - v0
        a3 = v1

        return a0 * f2 * factor + a1 * f2 + a2 * factor + a3


    @numba.njit
    def _catmull_rom_interpolation(v0, v1, v2, v3, factor):
        f2 = factor ** 2
        a0 = v0 * -0.5 + v1 * 1.5 - v2 * 1.5 + v3 * 0.5
        a1 = v0 - v1 * 2.5 + v2 * 2 - v3 * 0.5
        a2 = v0 * -0.5 + v2 * 0.5
        a3 = v1

        return a0 * f2 * factor + a1 * f2 + a2 * factor + a3


    @numba.njit
    def _extend_polylines(polylines):
        """Except list of polylines which are lists of vertices. Add extra points
        ot the start and end of them repeating previous edge slope."""
        v1 = verts[..., 0, :]
        v2 = verts[..., 1, :]
        v0 = v1 + v1 - v2
        last = verts[..., -1, :]
        prev = verts[..., -2, :]
        new_last = last + last - prev
        new_verts = ak.concatenate([v0[:, np.newaxis], verts, new_last[:, np.newaxis]], axis=1)
        return new_verts


    @numba.njit
    def _connect_polyline(verts):
        if verts.ndim == 2:
            edges = np.zeros((len(verts)-1, 2), dtype=np.int64)
            for i in range(len(edges)):
                edges[i] = [i, i+1]
            return edges, None
        elif verts.ndim == 3:
            verts_num = [len(v_obj) for v_obj in verts]
            edges_num = np.array([n-1 for n in verts_num])
            total_num = sum(edges_num)
            edges = np.zeros((total_num, 2), dtype=np.int64)
            edge_indexes = [i for n in edges_num for i in range(n)]
            for i, ei in enumerate(edge_indexes):
                edges[i] = [ei, ei+1]
            return edges, edges_num
        else:
            raise TypeError("Number of dimensions is not in range: 1 < n < 3")

    @numba.njit
    def f(a):
        return sum(a)
