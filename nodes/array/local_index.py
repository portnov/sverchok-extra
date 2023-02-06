# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import IntProperty

from sverchok.node_tree import SverchCustomTreeNode

try:
    import awkward as ak
except ImportError:
    ak = None


class SvLocalIndexNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvLocalIndexNode'
    bl_label = 'Local Index'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    axis: IntProperty(default=-1, update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'axis')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        self.outputs.new('SvStringsSocket', 'Data')

    def process(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=None)
        if data is None:
            return
        indexes = ak.local_index(data, axis=self.axis)
        self.outputs[0].sv_set(indexes)


register, unregister = bpy.utils.register_classes_factory([SvLocalIndexNode])
