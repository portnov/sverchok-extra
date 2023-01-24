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


class SvInputArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvInputArrayNode'
    bl_label = 'Input Array'
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
        for sock in self.inputs:
            if sock.bl_idname != self.sock_types[mode]:
                sock = sock.replace_socket(self.sock_types[mode])
            self.set_socket_prop(sock)
        if self.outputs[0].bl_idname != self.sock_types[mode]:
            self.outputs[0].replace_socket(self.sock_types[mode])
        self.process_node(context)

    type_mode: EnumProperty(
        name='Number Type',
        items=type_modes,
        update=mode_change)

    def size_change(self, context):
        mode = self.type_mode
        diff = self.size - len(self.inputs)
        for _ in range(diff):
            sock = self.inputs.new(self.sock_types[mode], 'Data')
            self.set_socket_prop(sock)
        for _ in range(-diff):
            self.inputs.remove(self.inputs[-1])
        self.process_node(context)

    def set_socket_prop(self, socket):
        mode = self.type_mode
        socket.use_prop = True
        if mode == 'INT':
            socket.default_property_type = 'int'
        elif mode == 'FLOAT':
            socket.default_property_type = 'float'
        elif mode == 'VECTOR':
            socket.expanded = True

    size: IntProperty(default=1, min=0, soft_max=10, max=1000, update=size_change)

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, "type_mode", text="")
        layout.prop(self, "size")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data").use_prop = True
        self.outputs.new('SvStringsSocket', "Data")

    def process(self):
        data = []
        for sock in self.inputs:
            if sock.is_linked:
                data.append([sock.sv_get(deepcopy=False)])
            else:
                val = sock.sv_get(deepcopy=False)
                if self.type_mode == 'VECTOR':
                    data.append([list(val[0][0])])
                else:
                    data.append(val[0])

        out = ak.concatenate(data) if data else ak.Array([])
        self.outputs[0].sv_set(out)


register, unregister = bpy.utils.register_classes_factory([SvInputArrayNode])
