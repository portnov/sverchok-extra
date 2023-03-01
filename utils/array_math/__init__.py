# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import numpy as np

from .array_numba import add_numba_implementation

try:
    import awkward as ak
except ImportError:
    ak = None


def slices(item, axis: int) -> tuple:
    empty = slice(None, None, None)
    items = []
    if axis >= 0:
        for _ in range(axis):
            items.append(empty)
        items.append(item)
        items = tuple(items)
    else:
        for _ in range(abs(axis) - 1):
            items.append(empty)
        items.append(item)
        items.append(...)
        items.reverse()
    return tuple(items)


def flatten(array, deep=-1):
    """Flattens array to the given deep. Return flattened array and a sequence
    ot unflatten it back. It does not work with all arrays."""
    num = deep if deep >= 0 else array.ndim + deep
    counts = []
    for _ in range(num):
        counts.append(ak.num(array))
        array = ak.flatten(array)
    if counts:
        counts = ak.concatenate([c[np.newaxis] for c in reversed(counts)])
    else:
        counts = ak.Array([])
    return array, counts


def unflatten(array, counts):
    """Use together with `flatten`"""
    for count in counts:
        array = ak.unflatten(array, count)
    return array


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


def apply_matrix_4x4(verts, matrices):
    if verts.ndim == 2:
        v1 = ak.concatenate([verts, [[1]]], axis=-1)
        m = matrices[np.newaxis] if matrices.ndim == 2 else matrices
    elif verts.ndim == 3:
        v1 = ak.concatenate([verts, ak.Array([[1]])[np.newaxis]], axis=-1)
        if matrices.ndim == 2:
            m = matrices[np.newaxis, np.newaxis]
        elif matrices.ndim == 3:
            m = matrices[:, np.newaxis]
        else:
            m = matrices
    else:
        raise TypeError(f"{verts.ndim=}, only 2 or 3 is supported")
    v2 = v1[..., np.newaxis, :]
    v3 = m * v2
    v4 = ak.sum(v3, axis=-1)
    v5 = v4[..., :-1]
    return v5


def apply_matrix_3x3(verts, matrices):
    if verts.ndim == 2:
        m = matrices[np.newaxis] if matrices.ndim == 2 else matrices
    elif verts.ndim == 3:
        if matrices.ndim == 2:
            m = matrices[np.newaxis, np.newaxis]
        elif matrices.ndim == 3:
            m = matrices[:, np.newaxis]
        else:
            m = matrices
    else:
        raise TypeError(f"{verts.ndim=}, only 2 or 3 is supported")
    v1 = verts[..., np.newaxis, :]
    v2 = m * v1
    v3 = ak.sum(v2, axis=-1)
    return v3


def matrix(positions, scale):
    pos, sc = ak.broadcast_arrays(positions, scale)
    v0, v1, _ = ak.broadcast_arrays(0, 1, positions[..., 0])
    w = ..., np.newaxis
    i1 = ak.concatenate([sc[..., 0][w], v0[w], v0[w], pos[..., 0][w]], axis=-1)
    i2 = ak.concatenate([v0[w], sc[..., 1][w], v0[w], pos[..., 1][w]], axis=-1)
    i3 = ak.concatenate([v0[w], v0[w], sc[..., 2][w], pos[..., 2][w]], axis=-1)
    i4 = ak.concatenate([v0[w], v0[w], v0[w], v1[w]], axis=-1)
    m = ak.concatenate([i1[..., np.newaxis, :], i2[..., np.newaxis, :], i3[..., np.newaxis, :], i4[..., np.newaxis, :]], axis=-2)
    return m


def euler_to_matrix(euler):
    # https://euclideanspace.com/maths/geometry/rotations/conversions/eulerToMatrix/index.htm
    w = ..., np.newaxis
    w1 = ..., np.newaxis, slice(None, None, None)
    ch = np.cos(euler[..., 1])
    sh = np.sin(euler[..., 1])
    ca = np.cos(euler[..., 2])
    sa = np.sin(euler[..., 2])
    cb = np.cos(euler[..., 0])
    sb = np.sin(euler[..., 0])

    m00 = ch * ca
    m01 = sh * sb - ch * sa * cb
    m02 = ch * sa * sb + sh * cb
    m10 = sa
    m11 = ca * cb
    m12 = -ca * sb
    m20 = -sh * ca
    m21 = sh * sa * cb + ch * sb
    m22 = -sh * sa * sb + ch * cb

    row1 = ak.concatenate([m00[w], m01[w], m02[w]], axis=-1)
    row2 = ak.concatenate([m10[w], m11[w], m12[w]], axis=-1)
    row3 = ak.concatenate([m20[w], m21[w], m22[w]], axis=-1)
    m = ak.concatenate([row1[w1], row2[w1], row3[w1]], axis=-2)
    return m


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


# @add_numba_implementation
def subdivide_polyline(verts, cuts, interpolation='LINEAR'):
    """Only works with list of polylines"""
    lines_mum = len(verts)
    segment_num = ak.num(verts, axis=-2) - 1
    segment_shape = ak.num(verts, axis=-1)[..., :-1]
    _, count_per_seg = ak.broadcast_arrays(segment_shape, cuts)
    total_num = ak.sum(count_per_seg) + ak.sum(segment_num)
    seg_weight0 = np.zeros(total_num)
    seg_weight1 = ak.unflatten(seg_weight0, ak.flatten(count_per_seg)+1)
    seg_weight2 = ak.unflatten(seg_weight1, segment_num)
    seg_weight3 = ak.local_index(seg_weight2)
    seg_weight = seg_weight3 / (count_per_seg+1)
    if interpolation == 'LINEAR':
        vert1 = verts[..., :-1, :]
        vert1 = vert1[..., np.newaxis, :]
        vert2 = verts[..., 1:, :]
        vert2 = vert2[..., np.newaxis, :]
        new_verts = linear_interpolation(vert1, vert2, seg_weight)
    elif interpolation in {'CUBIC', 'CATMULL_ROM'}:
        extra_verts = extend_polyline(verts)
        v0 = extra_verts[..., :-3, :]
        v0 = v0[..., np.newaxis, :]
        v1 = extra_verts[..., 1:-2, :]
        v1 = v1[..., np.newaxis, :]
        v2 = extra_verts[..., 2:-1, :]
        v2 = v2[..., np.newaxis, :]
        v3 = extra_verts[..., 3:, :]
        v3 = v3[..., np.newaxis, :]
        if interpolation == 'CUBIC':
            new_verts = cubic_interpolation(v0, v1, v2, v3, seg_weight)
        else:
            new_verts = catmull_rom_interpolation(v0, v1, v2, v3, seg_weight)
    else:
        raise TypeError(f"{interpolation=} is not among supported.")
    new_verts = ak.flatten(new_verts, axis=-2)
    new_verts = ak.concatenate([new_verts, verts[..., -1, :][..., np.newaxis, :]], axis=-2)
    return new_verts


@add_numba_implementation
def connect_polyline(verts):
    _, edge_shape = ak.broadcast_arrays(verts, 0, depth_limit=verts.ndim - 1)  # if cycle
    if verts.ndim == edge_shape.ndim:  # if verts are regular the broadcast is different
        edge_shape = ak.flatten(edge_shape, axis=-1)
    edge_shape = edge_shape[..., :-1]  # if not cycle
    edge_indexes = ak.local_index(edge_shape)
    edge_wrap_ind = edge_indexes[..., np.newaxis]
    edges = ak.concatenate([edge_wrap_ind, edge_wrap_ind + 1], axis=-1)
    return edges


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
    return v1 * (1-factor) + v2 * factor


def cubic_interpolation(v0, v1, v2, v3, factor):
    f2 = factor**2
    a0 = v3-v2-v0+v1
    a1 = v0-v1-a0
    a2 = v2-v0
    a3 = v1

    return a0 * f2 * factor + a1 * f2 + a2 * factor + a3


def catmull_rom_interpolation(v0, v1, v2, v3, factor):
    f2 = factor**2
    a0 = v0 * -0.5 + v1 * 1.5 - v2 * 1.5 + v3 * 0.5
    a1 = v0 - v1 * 2.5 + v2 * 2 - v3 * 0.5
    a2 = v0 * -0.5 + v2 * 0.5
    a3 = v1

    return a0 * f2 * factor + a1 * f2 + a2 * factor + a3


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
