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


class SvArrRotateVectorNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrRotateVectorNode'
    bl_label = 'Rotate Vector (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vector').use_prop = True
        self.inputs.new('SvVerticesSocket', 'Rotation').use_prop = True
        self.outputs.new('SvVerticesSocket', 'Vector')

    def process(self):
        verts = self.inputs[0].sv_get(deepcopy=False)
        verts = verts if self.inputs[0].is_linked else ak.Array([list(verts[0][0])])
        euler = self.inputs[1].sv_get(deepcopy=False)
        euler = euler if self.inputs[1].is_linked else ak.Array([list(euler[0][0])])
        m = amath.euler_to_matrix(euler)
        new_verts = amath.apply_matrix_3x3(verts, m)
        self.outputs[0].sv_set(new_verts)


register, unregister = bpy.utils.register_classes_factory([SvArrRotateVectorNode])
