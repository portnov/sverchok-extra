# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import numpy as np

try:
    import awkward as ak
except ImportError:
    ak = None


def vert_length(verts):
    return ak.sum(verts ** 2, axis=-1) ** 0.5


def scale_vert(verts, scale):
    """
    >> v=scale_vert(ak.Array([[[1,1,1],[2,2,2],[3,3,3]],[[4,4,4],[5,5,5]]]), ak.Array([[10,20,0],[2,3]])).show(stream=None)
    >> print(v)
    [[[10, 10, 10], [40, 40, 40], [0, 0, 0]],
     [[8, 8, 8], [15, 15, 15]]]
    """
    return verts * scale[..., np.newaxis]


def repeat_array(a, repeats):
    pass


def segment_length(verts):
    """Distances between first and second vertices"""
    vert1 = verts[..., :-1, :]
    vert2 = verts[..., 1:, :]
    dist_vec = vert2 - vert1
    return vert_length(dist_vec)


def polyline_length(verts):
    """Sum of distances between all vectors innermost lists"""
    return ak.sum(segment_length(verts), axis=-1)


def subdivide_polyline(verts, cuts, interpolation='LINEAR'):
    """Only works with list of polylines"""
    lines_mum = len(verts)
    segment_num = ak.num(verts, axis=-2) - 1
    segment_shape = ak.num(verts, axis=-1)[..., :-1]
    _, count_per_seg = ak.broadcast_arrays(segment_shape, cuts)
    new_verts_num = segment_num * cuts + ak.num(verts)
    total_num = ak.sum(new_verts_num)
    seg_weight = np.zeros(total_num - lines_mum)
    seg_weight = ak.unflatten(seg_weight, ak.flatten(count_per_seg)+1)
    seg_weight = ak.unflatten(seg_weight, segment_num)
    seg_weight = ak.local_index(seg_weight)
    seg_weight = seg_weight / (count_per_seg+1)
    if interpolation == 'LINEAR':
        vert1 = verts[..., :-1, :]
        vert1, _ = ak.unzip(ak.cartesian([vert1[..., np.newaxis, :], seg_weight], axis=2))
        vert2 = verts[..., 1:, :]
        vert2, _ = ak.unzip(ak.cartesian([vert2[..., np.newaxis, :], seg_weight], axis=2))
        new_verts = linear_interpolation(vert1, vert2, seg_weight)
    elif interpolation in {'CUBIC', 'CATMULL_ROM'}:
        verts = extend_polyline(verts)
        v0 = verts[..., :-3, :]
        v0, _ = ak.unzip(ak.cartesian([v0[..., np.newaxis, :], seg_weight], axis=2))
        v1 = verts[..., 1:-2, :]
        v1, _ = ak.unzip(ak.cartesian([v1[..., np.newaxis, :], seg_weight], axis=2))
        v2 = verts[..., 2:-1, :]
        v2, _ = ak.unzip(ak.cartesian([v2[..., np.newaxis, :], seg_weight], axis=2))
        v3 = verts[..., 3:, :]
        v3, _ = ak.unzip(ak.cartesian([v3[..., np.newaxis, :], seg_weight], axis=2))
        if interpolation == 'CUBIC':
            new_verts = cubic_interpolation(v0, v1, v2, v3, seg_weight)
        else:
            new_verts = catmull_rom_interpolation(v0, v1, v2, v3, seg_weight)
    else:
        raise TypeError(f"{interpolation=} is not among supported.")
    new_verts = ak.flatten(new_verts, axis=-2)
    return new_verts


def extend_polyline(verts):
    """Except list of polylines which are lists of vertices. Add extra points
    ot the start and end of them repeating previous edge slope."""
    v1 = verts[..., 0, :]
    v2 = verts[..., 1, :]
    v0 = v1 + v1 - v2
    last = verts[..., -1, :]
    prev = verts[..., -2, :]
    new_last = last + last - prev
    new_verts = ak.concatenate([v0[:,np.newaxis], verts, new_last[:,np.newaxis]], axis=1)
    return new_verts


# http://www.paulbourke.net/miscellaneous/interpolation/
def linear_interpolation(v1, v2, factor):
    return scale_vert(v1, 1-factor) + scale_vert(v2, factor)


def cubic_interpolation(v0, v1, v2, v3, factor):
    f2 = factor**2
    a0 = v3-v2-v0+v1
    a1 = v0-v1-a0
    a2 = v2-v0
    a3 = v1

    return scale_vert(a0, f2 * factor) + scale_vert(a1, f2) + scale_vert(a2, factor) + a3


def catmull_rom_interpolation(v0, v1, v2, v3, factor):
    A = ak.Array
    f2 = factor**2
    a0 = scale_vert(v0, A([-0.5])) + scale_vert(v1, A([1.5])) - scale_vert(v2, A([1.5])) + scale_vert(v3, A([0.5]))
    a1 = v0 - scale_vert(v1, A([2.5])) + scale_vert(v2, A([2])) - scale_vert(v3, A([0.5]))
    a2 = scale_vert(v0, A([-0.5])) + scale_vert(v2, A([0.5]))
    a3 = v1

    return scale_vert(a0, f2 * factor) + scale_vert(a1, f2) + scale_vert(a2, factor) + a3


def cosine_interpolation(v1, v2, factor):
    ft = factor * 3.1415927
    f = (1 - np.cos(ft)) * 0.5
    return scale_vert(v1, 1-f) + scale_vert(v2, f)


if __name__ == '__main__':
    p_line = ak.Array([[[0, 0, 0], [1.5, 0, 0], [2, 0.5, 0]],
                       [[0, 0, 0], [0, 1.5, 0], [0, 2, 0.5], [0, 3, 0]]])
    new_line = subdivide_polyline(p_line, ak.Array([1]))
    # from timeit import timeit
    # t=timeit('subdivide_polyline(p_line, ak.Array([5]))', 'from __main__ import ak, subdivide_polyline, p_line', number=1)
    # print(t)
