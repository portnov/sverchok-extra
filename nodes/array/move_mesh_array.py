# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from copy import copy

import numpy as np
try:
    import awkward as ak
except ImportError:
    ak = None

import bpy

from sverchok.node_tree import SverchCustomTreeNode


class SvArrMoveMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Moves Vertices array
    Tooltip: Moves vectors based in another vector set and a multipier factor
    """
    bl_idname = 'SvArrMoveMeshNode'
    bl_label = 'Move Mesh (Array)'
    bl_icon = 'ORIENTATION_VIEW'
    sv_icon = 'SV_MOVE'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Array')
        self.inputs.new('SvVerticesSocket', 'Movement Vectors').use_prop = True
        s = self.inputs.new('SvStringsSocket', 'Factor')
        s.use_prop = True
        s.default_float_property = 1.0
        self.outputs.new('SvStringsSocket', 'Array')

    def process(self):
        mesh = self.inputs['Array'].sv_get(deepcopy=False, default=None)
        if mesh is None:
            return
        mesh = copy(mesh)
        move = self.inputs['Movement Vectors'].sv_get(deepcopy=False)
        if not self.inputs['Movement Vectors'].is_linked:
            move = ak.Array(move[0][0])[np.newaxis, np.newaxis]  # https://github.com/scikit-hep/awkward/discussions/2118
        factor = self.inputs['Factor'].sv_get(deepcopy=False)
        if not self.inputs['Factor'].is_linked:
            factor = factor[0][0]

        mesh['verts'] = mesh.verts + move * factor
        self.outputs[0].sv_set(mesh)


register, unregister = bpy.utils.register_classes_factory([SvArrMoveMeshNode])
