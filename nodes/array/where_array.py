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


class SvWhereArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvWhereArrayNode'
    bl_label = 'Where Array'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Condition')
        self.inputs.new('SvStringsSocket', 'False')
        self.inputs.new('SvStringsSocket', 'True')
        self.outputs.new('SvStringsSocket', 'Data')

    def sv_update(self):
        in1 = self.inputs[0]
        type1 = 'SvStringsSocket' if not in1.is_linked else in1.other.bl_idname
        in2 = self.inputs[1]
        type2 = 'SvStringsSocket' if not in2.is_linked else in2.other.bl_idname
        out_type = type1 if type1 == type2 else 'SvStringsSocket'
        if self.outputs[0].bl_idname != out_type:
            self.outputs[0].replace_socket(out_type)

    def process(self):
        condition = self.inputs['Condition'].sv_get(deepcopy=False, default=None)
        if condition is None:
            return
        false = self.inputs['False'].sv_get(deepcopy=False, default=None)
        true = self.inputs['True'].sv_get(deepcopy=False, default=None)
        if false is not None or true is not None:
            result = ak.where(condition, true, false)
        else:
            result = ak.where(condition)
        self.outputs[0].sv_set(result)


register, unregister = bpy.utils.register_classes_factory([SvWhereArrayNode])
