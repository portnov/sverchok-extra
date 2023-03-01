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
from bpy.props import IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode


class SvFlatteningArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvFlatteningArrayNode'
    bl_label = 'Flattening Array'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    deep: IntProperty(default=-1, update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'deep')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        self.outputs.new('SvStringsSocket', 'Data')
        self.outputs.new('SvStringsSocket', 'Counts')

    def process(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=None)
        if data is None:
            return
        num = self.deep if self.deep >= 0 else data.ndim+self.deep
        counts = []
        for _ in range(num):
            counts.append(ak.num(data))
            data = ak.flatten(data)
        if counts:
            counts = ak.concatenate([c[np.newaxis] for c in reversed(counts)])
        else:
            counts = ak.Array([])
        self.outputs[0].sv_set(data)
        self.outputs[1].sv_set(counts)


register, unregister = bpy.utils.register_classes_factory([SvFlatteningArrayNode])
