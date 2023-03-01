# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok_extra.utils import array_math as amath

try:
    import awkward as ak
except ImportError:
    ak = None


class SvArrMatrixInNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrMatrixInNode'
    bl_label = 'Matrix in (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Position').use_prop = True
        s = self.inputs.new('SvVerticesSocket', 'Scale')
        s.use_prop = True
        s.default_property = 1, 1, 1
        self.outputs.new('SvMatrixSocket', 'Matrix')

    def process(self):
        pos = self.inputs[0].sv_get(deepcopy=False)
        pos = pos if self.inputs[0].is_linked else ak.Array([list(pos[0][0])])
        scale = self.inputs[1].sv_get(deepcopy=False)
        scale = scale if self.inputs[1].is_linked else ak.Array([list(scale[0][0])])
        self.outputs[0].sv_set(amath.matrix(pos, scale))


register, unregister = bpy.utils.register_classes_factory([SvArrMatrixInNode])
