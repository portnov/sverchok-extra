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


class SvArrMoveVerticesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Moves Vertices array
    Tooltip: Moves vectors based in another vector set and a multipier factor
    """
    bl_idname = 'SvArrMoveVerticesNode'
    bl_label = 'Move Vertices (Array)'
    bl_icon = 'ORIENTATION_VIEW'
    sv_icon = 'SV_ALPHA'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvVerticesSocket', 'Movement Vectors').use_prop = True
        s = self.inputs.new('SvStringsSocket', 'Factor')
        s.use_prop = True
        s.default_float_property = 1.0
        self.outputs.new('SvVerticesSocket', 'Vertices')

    def process(self):
        verts = self.inputs['Vertices'].sv_get(deepcopy=False, default=None)
        if verts is None:
            self.outputs[0].sv_set([])
            return
        move = self.inputs['Movement Vectors'].sv_get(deepcopy=False)
        if not self.inputs['Movement Vectors'].is_linked:
            move = ak.Array(move[0][0])[np.newaxis, np.newaxis]  # https://github.com/scikit-hep/awkward/discussions/2118
        factor = self.inputs['Factor'].sv_get(deepcopy=False)
        if not self.inputs['Factor'].is_linked:
            factor = factor[0][0]
        result = verts + move * factor
        self.outputs[0].sv_set(result)


register, unregister = bpy.utils.register_classes_factory([SvArrMoveVerticesNode])
