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
from bpy.props import IntProperty

from sverchok.node_tree import SverchCustomTreeNode


class SvUnflatteningArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvUnflatteningArrayNode'
    bl_label = 'Unflattening Array'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        self.inputs.new('SvStringsSocket', 'Counts')
        self.outputs.new('SvStringsSocket', 'Data')

    def process(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=None)
        counts = self.inputs[1].sv_get(deepcopy=False, default=None)
        if counts is None:
            if data is not None:
                self.outputs[0].sv_set(data)
            return
        if data is None:
            return
        for count in counts:
            data = ak.unflatten(data, count)
        self.outputs[0].sv_set(data)


register, unregister = bpy.utils.register_classes_factory([SvUnflatteningArrayNode])
