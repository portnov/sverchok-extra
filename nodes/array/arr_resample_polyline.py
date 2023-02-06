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
from sverchok_extra.utils import array_math as amath


class SvResamplePolylineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvResamplePolylineNode'
    bl_label = 'Resample Polyline (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Array')
        s = self.inputs.new('SvStringsSocket', 'Count')
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 10
        self.outputs.new('SvStringsSocket', 'Array')

    def process(self):
        line = self.inputs[0].sv_get(deepcopy=False, default=None)
        if line is None:
            return
        count = self.inputs[1].sv_get(deepcopy=False)
        count = count if self.inputs[1].is_linked else ak.Array(count[0])
        segment_len = amath.segment_length(line.verts)
        line_len = ak.sum(segment_len, axis=-1)
        step = line_len / count
        segment_count = ak.values_astype(segment_len / step, int)
        total_num = ak.sum(count)
        new_verts = np.zeros((total_num, 3))
        new_verts = ak.unflatten(new_verts, count)
        vert1 = line.verts[..., :-1, :]
        vert2 = line.verts[..., 1:, :]
        breakpoint()
        self.outputs[0].sv_set(line)


register, unregister = bpy.utils.register_classes_factory([SvResamplePolylineNode])
