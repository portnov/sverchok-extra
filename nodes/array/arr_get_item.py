# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok_extra.utils import array_math as amath

try:
    import awkward as ak
except ImportError:
    ak = None


class SvArrGetItemNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrGetItemNode'
    bl_label = 'Get Item (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    axis: IntProperty(update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'axis')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        s = self.inputs.new('SvStringsSocket', 'Index')
        s.use_prop = True
        s.default_property_type = 'int'
        self.outputs.new('SvStringsSocket', 'Data')

    def sv_update(self):
        in_s = self.inputs[0]
        out_type = 'SvStringsSocket' if not in_s.is_linked else in_s.other.bl_idname
        if self.outputs[0].bl_idname != out_type:
            self.outputs[0].replace_socket(out_type)

    def process(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=None)
        if data is None:
            return
        where = self.inputs[1].sv_get(deepcopy=False)
        where = where if self.inputs[1].is_linked else where[0][0]
        data = data[amath.slices(where, axis=self.axis)]
        self.outputs[0].sv_set(data)


register, unregister = bpy.utils.register_classes_factory([SvArrGetItemNode])
