# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

try:
    import awkward as ak
except ImportError:
    ak = None

import bpy

from sverchok.node_tree import SverchCustomTreeNode


class SvArrPolylineLengthNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrPolylineLengthNode'
    bl_label = 'Polyline Length (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Array')
        self.outputs.new('SvStringsSocket', 'Line Length')
        self.outputs.new('SvStringsSocket', 'Segment Length')

    def process(self):
        line = self.inputs[0].sv_get(deepcopy=False, default=None)
        if line is None:
            return
        vert1 = line.verts[..., :-1, :]
        vert2 = line.verts[..., 1:, :]
        dist_vec = vert2 - vert1
        segment_len = ak.sum(dist_vec**2, axis=-1)**0.5
        line_len = ak.sum(segment_len, axis=-1)
        self.outputs['Line Length'].sv_set(line_len)
        self.outputs['Segment Length'].sv_set(segment_len)


register, unregister = bpy.utils.register_classes_factory([SvArrPolylineLengthNode])
