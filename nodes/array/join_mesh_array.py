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


class SvArrJoinMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
     Triggers: array
     Tooltip:
     """
    bl_idname = 'SvArrJoinMeshNode'
    bl_label = 'Join Mesh (Array)'
    sv_icon = 'SV_ALPHA'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Array')
        self.outputs.new('SvStringsSocket', 'Array')

    def process(self):
        mesh = self.inputs['Array'].sv_get(deepcopy=False, default=None)
        if mesh is None:
            return

        verts_num = ak.num(mesh.verts)  # [2, 1, 3, 2]
        cum_num = np.cumsum(verts_num)  # [2, 3, 6, 8]
        previous_num = cum_num - verts_num  # [0, 2, 3, 6]
        verts = ak.flatten(mesh.verts, axis=1)[np.newaxis]
        out_mesh = {'verts': verts}
        if 'edges' in mesh.fields:
            edges = mesh.edges + previous_num
            out_mesh['edges'] = ak.flatten(edges, axis=1)[np.newaxis]
        if 'faces' in mesh.fields:
            faces = mesh.faces + previous_num
            out_mesh['faces'] = ak.flatten(faces, axis=1)[np.newaxis]
        self.outputs[0].sv_set(ak.Array(out_mesh))


register, unregister = bpy.utils.register_classes_factory([SvArrJoinMeshNode])
