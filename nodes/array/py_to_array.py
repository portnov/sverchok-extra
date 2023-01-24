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


class SvPyToArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvPyToArrayNode'
    bl_label = 'Python to Array'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

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
        self.outputs[0].sv_set(ak.Array(data))


register, unregister = bpy.utils.register_classes_factory([SvPyToArrayNode])
