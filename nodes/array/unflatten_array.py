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
from bpy.props import IntProperty

from sverchok.node_tree import SverchCustomTreeNode


class SvUnflattenArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvUnflattenArrayNode'
    bl_label = 'Unflatten Array'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    axis: IntProperty(update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'axis')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        s = self.inputs.new('SvStringsSocket', 'Counts')
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 1
        self.outputs.new('SvStringsSocket', 'Data')

    def sv_update(self):
        in_s = self.inputs[0]
        out_type = 'SvStringsSocket' if not in_s.is_linked else in_s.other.bl_idname
        if self.outputs[0].bl_idname != out_type:
            self.outputs[0].replace_socket(out_type)

    def process(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=None)
        if data is None:
            self.outputs[0].sv_set(ak.Array([]))
            return
        counts = self.inputs[1].sv_get(deepcopy=False)
        if not self.inputs[1].is_linked:
            counts = counts[0][0]
        # if len(counts) == 1 and isinstance(counts[0], (int, float)):
        #     counts = counts[0]
        data = ak.unflatten(data, counts, axis=self.axis)
        self.outputs[0].sv_set(data)


register, unregister = bpy.utils.register_classes_factory([SvUnflattenArrayNode])
