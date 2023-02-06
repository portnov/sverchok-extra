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


class SvArrVectorInNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrVectorInNode'
    bl_label = 'Vector in (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "X").use_prop = True
        self.inputs.new('SvStringsSocket', "Y").use_prop = True
        self.inputs.new('SvStringsSocket', "Z").use_prop = True
        self.outputs.new('SvVerticesSocket', "Vectors")
        self.width = 100

    def process(self):
        x = self.inputs[0].sv_get(deepcopy=False)
        x = x if self.inputs[0].is_linked else x[0][0]
        x = x[..., np.newaxis] if hasattr(x, '__len__') else x
        y = self.inputs[1].sv_get(deepcopy=False)
        y = y if self.inputs[1].is_linked else y[0][0]
        y = y[..., np.newaxis] if hasattr(y, '__len__') else y
        z = self.inputs[2].sv_get(deepcopy=False)
        z = z if self.inputs[2].is_linked else z[0][0]
        z = z[..., np.newaxis] if hasattr(z, '__len__') else z
        if not any(s.is_linked for s in self.inputs):
            self.outputs[0].sv_set(ak.Array([x, y, z]))
            return
        x, y, z = ak.broadcast_arrays(x, y, z)
        # out = np.column_stack([x, y, z])
        out = ak.concatenate([x, y, z], axis=-1)
        self.outputs[0].sv_set(out)


register, unregister = bpy.utils.register_classes_factory([SvArrVectorInNode])
