# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from copy import copy

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok_extra.utils import array_math as amath

try:
    import awkward as ak
except ImportError:
    ak = None


class SvArrMatrixTransformNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrMatrixTransformNode'
    bl_label = 'Apply Matrix (Array)'
    sv_icon = 'SV_ALPHA'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Array")
        self.inputs.new('SvMatrixSocket', "Matrices")

        self.outputs.new('SvStringsSocket', "Array")

    def process(self):
        mesh = self.inputs[0].sv_get(default=None, deepcopy=False)
        matrices = self.inputs[1].sv_get(default=None, deepcopy=False)
        if mesh is None or matrices is None:
            if mesh is not None:
                self.outputs[0].sv_set(mesh)
            return

        verts = amath.apply_matrix_4x4(mesh.verts, matrices)
        me = copy(mesh)
        me['verts'] = verts
        self.outputs[0].sv_set(me)


register, unregister = bpy.utils.register_classes_factory([SvArrMatrixTransformNode])
