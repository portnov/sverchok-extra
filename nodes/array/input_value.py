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
from bpy.props import EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode


class SvInputValueNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvInputValueNode'
    bl_label = 'Input Value'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    type_modes = [
        ("FLOAT", "Float", "", 0),
        ("INT", "Integer", "", 1),
        ("VECTOR", "Vector", "", 2),
    ]

    sock_types = {'FLOAT': 'SvStringsSocket',
                  'INT': 'SvStringsSocket',
                  'VECTOR': 'SvVerticesSocket'}

    def mode_change(self, context):
        mode = self.type_mode
        sock = self.inputs[0]
        if sock.bl_idname != self.sock_types[mode]:
            sock = sock.replace_socket(self.sock_types[mode])
        mode = self.type_mode
        sock.use_prop = True
        if mode == 'INT':
            sock.default_property_type = 'int'
        elif mode == 'FLOAT':
            sock.default_property_type = 'float'
        elif mode == 'VECTOR':
            sock.expanded = True
        if self.outputs[0].bl_idname != self.sock_types[mode]:
            self.outputs[0].replace_socket(self.sock_types[mode])
        self.process_node(context)

    type_mode: EnumProperty(
        name='Number Type',
        items=type_modes,
        update=mode_change)

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, "type_mode", text="")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data").use_prop = True
        self.outputs.new('SvStringsSocket', "Data")
        self.width = 100

    def process(self):
        sock = self.inputs[0]
        if sock.is_linked:
            data = sock.sv_get(deepcopy=False)
            for _ in range(100):
                if isinstance(data, (float, int)):
                    value = data
                    break
                data = data[0]
            else:
                raise RuntimeError("Was not able to extract value from the input data")
        else:
            val = sock.sv_get(deepcopy=False)
            if self.type_mode == 'VECTOR':
                value = ak.Array(list(val[0][0]))
            else:
                value = val[0][0]

        self.outputs[0].sv_set(value)


register, unregister = bpy.utils.register_classes_factory([SvInputValueNode])
