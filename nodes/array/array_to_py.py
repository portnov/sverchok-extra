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
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode


class SvArrayToPyNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrayToPyNode'
    bl_label = 'Array to Python'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    to_numpy: BoolProperty()

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'to_numpy')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        self.outputs.new('SvStringsSocket', 'Data')

    def sv_update(self):
        in_s = self.inputs[0]
        out_type = 'SvStringsSocket' if not in_s.is_linked else in_s.other.bl_idname
        if self.outputs[0].bl_idname != out_type:
            self.outputs[0].replace_socket(out_type)

    def process(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=[])
        if self.to_numpy:
            self.outputs[0].sv_set(ak.to_numpy(data))
        else:
            self.outputs[0].sv_set(ak.to_list(data))


register, unregister = bpy.utils.register_classes_factory([SvArrayToPyNode])
