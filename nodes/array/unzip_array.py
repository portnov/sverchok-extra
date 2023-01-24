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


class SvUnzipArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvUnzipArrayNode'
    bl_label = 'Unzip Arrays'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')

    def sv_update(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=None)
        if data is None or not hasattr(data, 'fields'):
            self.outputs.clear()
            return

        diff = len(data.fields) - len(self.outputs)
        for _ in range(diff):
            self.outputs.new('SvStringsSocket', '')
        for _ in range(-diff):
            self.outputs.remove(self.outputs[-1])

        for name, sock in zip(data.fields, self.outputs):
            sock.name = name

    def process(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=None)
        if data is None:
            return
        out = ak.unzip(data)
        for out_data, sock in zip(out, self.outputs):
            sock.sv_set(out_data)


register, unregister = bpy.utils.register_classes_factory([SvUnzipArrayNode])
