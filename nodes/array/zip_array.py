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
from bpy.props import IntProperty

from sverchok.node_tree import SverchCustomTreeNode


class SvZipArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvZipArrayNode'
    bl_label = 'Zip Arrays'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    depth_limit: IntProperty(update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'depth_limit')

    def sv_init(self, context):
        self.inputs.new('SvTextSocket', 'Data').custom_draw = 'draw_field'
        self.outputs.new('SvStringsSocket', 'Data')

    def sv_update(self):
        if self.inputs[-1].is_linked:
            self.inputs.new('SvTextSocket', 'Data').custom_draw = 'draw_field'

        back_inp = list(self.inputs)[::-1]
        empty = len(list(takewhile(lambda s: not s.is_linked, back_inp)))
        for _ in range(empty - 1):
            self.inputs.remove(self.inputs[-1])

        others = {s.other.bl_idname for s in self.inputs if s.is_linked}
        out_type = 'SvStringsSocket' if len(others) != 1 else others.pop()
        if self.outputs[0].bl_idname != out_type:
            self.outputs[0].replace_socket(out_type)

    def draw_field(self, socket, context, layout):
        layout.prop(socket, 'default_property', text='')

    def process(self):
        arrays = [s.sv_get(deepcopy=False) for s in self.inputs if s.is_linked]
        if not arrays:
            return
        fields = [s.default_property for s in self.inputs if s.is_linked]
        depth_limit = self.depth_limit if self.depth_limit else None
        if any(fields):
            out = ak.zip({n: d for n, d in zip(fields, arrays)},
                         depth_limit=depth_limit)
        else:
            out = ak.zip(arrays, depth_limit=depth_limit)
        self.outputs[0].sv_set(out)


register, unregister = bpy.utils.register_classes_factory([SvZipArrayNode])
