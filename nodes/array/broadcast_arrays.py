# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import takewhile

try:
    import awkward as ak
except ImportError:
    ak = None

import bpy
from bpy.props import IntProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode


class SvBroadcastArraysNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvBroadcastArraysNode'
    bl_label = 'Broadcast arrays'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    broadcust_rules = [
        ("one_to_one", "One to One", "", 0),
        ("intersect", "Intersect", "", 1),
        ("all_or_nothing", "All or Nothing", "", 2),
        ("none", "None", "", 3),
    ]

    broadcust_rule: EnumProperty(items=broadcust_rules,
                                 update=lambda s, c: s.process_node(c))
    depth_limit: IntProperty(update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'broadcust_rule', text='')
        layout.prop(self, 'depth_limit')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')

    def sv_update(self):
        if self.inputs[-1].is_linked:
            self.inputs.new('SvStringsSocket', 'Data')
            self.outputs.new('SvStringsSocket', 'Data')

        back_inp = list(self.inputs)[::-1]
        empty = len(list(takewhile(lambda s: not s.is_linked, back_inp)))
        for _ in range(empty - 1):
            self.inputs.remove(self.inputs[-1])
            self.outputs.remove(self.outputs[-1])

        for in_s, out_s in zip(self.inputs, self.outputs):
            out_type = 'SvStringsSocket' if not in_s.is_linked\
                else in_s.other.bl_idname
            if out_s.bl_idname != out_type:
                out_s.replace_socket(out_type)

    def process(self):
        arrays = [s.sv_get(deepcopy=False) for s in self.inputs if s.is_linked]
        if not arrays:
            return
        depth_limit = self.depth_limit if self.depth_limit else None
        arrays = ak.broadcast_arrays(
            *arrays,
            depth_limit=depth_limit,
            broadcast_parameters_rule=self.broadcust_rule)

        arr_index = 0
        for in_s, out_s in zip(self.inputs, self.outputs):
            if in_s.is_linked:
                out_s.sv_set(arrays[arr_index])
                arr_index += 1


register, unregister = bpy.utils.register_classes_factory([SvBroadcastArraysNode])
