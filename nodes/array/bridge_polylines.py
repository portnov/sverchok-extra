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


class SvArrBridgePolylinesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrBridgePolylinesNode'
    bl_label = 'Bridge Polylines (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Array')
        self.outputs.new('SvStringsSocket', 'Array')

    def process(self):
        line = self.inputs[0].sv_get(deepcopy=False, default=None)
        if line is None:
            return
        verts = line.verts
        points_num = ak.num(verts, axis=-2)[..., 0]
        lines_num = ak.num(verts, axis=-3)
        line_index = ak.local_index(line.edges, axis=-3)
        new_edges = line.edges + line_index * points_num
        edge1 = new_edges[..., :-1, :, :]
        edge2 = new_edges[..., 1:, :, :][..., ::-1]
        faces = ak.concatenate([edge1, edge2], axis=-1)
        faces = ak.flatten(faces, axis=-2)
        verts = ak.flatten(verts, axis=-2)
        if verts.ndim == 2:
            verts, faces = verts[np.newaxis], faces[np.newaxis]
        polyline = ak.Array({'verts': verts, 'faces': faces})
        self.outputs[0].sv_set(polyline)


register, unregister = bpy.utils.register_classes_factory([SvArrBridgePolylinesNode])
