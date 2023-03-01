# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from copy import copy
from itertools import takewhile

import bpy

from sverchok.node_tree import SverchCustomTreeNode

try:
    import awkward as ak
except ImportError:
    ak = None


class SvSetFieldNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvSetFieldNode'
    bl_label = 'Set Field'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Array')
        self.inputs.new('SvTextSocket', 'Data').custom_draw = 'draw_field'
        self.outputs.new('SvStringsSocket', 'Array')

    def sv_update(self):
        if self.inputs[-1].is_linked:
            self.inputs.new('SvTextSocket', 'Data').custom_draw = 'draw_field'

        back_inp = list(self.inputs)[::-1]
        empty = len(list(takewhile(lambda s: not s.is_linked, back_inp)))
        for _ in range(empty - 2):
            self.inputs.remove(self.inputs[-1])

        others = {s.other.bl_idname for s in self.inputs[1:] if s.is_linked}
        out_type = 'SvStringsSocket' if len(others) != 1 else others.pop()
        if self.outputs[0].bl_idname != out_type:
            self.outputs[0].replace_socket(out_type)

    def draw_field(self, socket, context, layout):
        layout.prop(socket, 'default_property', text='')

    def process(self):
        arr = self.inputs['Array'].sv_get(deepcopy=False, default=None)
        if arr is None:
            return
        arr = copy(arr)
        arrays = [s.sv_get(deepcopy=False) for s in self.inputs[1:] if s.is_linked]
        fields = [s.default_property for s in self.inputs[1:] if s.is_linked]
        for f, a in zip(fields, arrays):
            if not f:
                continue
            arr[f] = a
        self.outputs[0].sv_set(arr)


register, unregister = bpy.utils.register_classes_factory([SvSetFieldNode])
