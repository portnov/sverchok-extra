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

import bpy

from sverchok.node_tree import SverchCustomTreeNode


class SvArrPolylineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrPolylineNode'
    bl_label = 'Polyline (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Array')

    def process(self):
        verts = self.inputs[0].sv_get(deepcopy=False, default=None)
        if verts is None:
            return
        _, edge_shape = ak.broadcast_arrays(verts, 0, depth_limit=verts.ndim-1)  # if cycle
        if verts.ndim == edge_shape.ndim:  # if verts are regular the broadcast is different
            edge_shape = ak.flatten(edge_shape, axis=-1)
        edge_shape = edge_shape[..., :-1]  # if not cycle
        edge_indexes = ak.local_index(edge_shape)
        edge_wrap_ind = edge_indexes[..., np.newaxis]
        edges = ak.concatenate([edge_wrap_ind, edge_wrap_ind+1], axis=-1)
        if verts.ndim == 2:
            verts, edges = verts[np.newaxis], edges[np.newaxis]
        polyline = ak.Array({'verts': verts, 'edges': edges})
        self.outputs[0].sv_set(polyline)


register, unregister = bpy.utils.register_classes_factory([SvArrPolylineNode])
