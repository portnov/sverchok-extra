# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from copy import copy

try:
    import awkward as ak
except ImportError:
    ak = None

import bpy

from sverchok.node_tree import SverchCustomTreeNode


class SvArrFlipMeshNormalsNode(SverchCustomTreeNode, bpy.types.Node):
    """
     Triggers: array
     Tooltip:
     """
    bl_idname = 'SvArrFlipMeshNormalsNode'
    bl_label = 'Flip Mesh Normals (Array)'
    sv_icon = 'SV_ALPHA'

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Array')
        self.inputs.new('SvStringsSocket', 'Mask')
        self.outputs.new('SvStringsSocket', 'Array')

    def process(self):
        mesh = self.inputs['Array'].sv_get(deepcopy=False, default=None)
        if mesh is None:
            return
        mask = self.inputs['Mask'].sv_get(deepcopy=False, default=None)
        mesh = copy(mesh)
        new_faces = mesh.faces[..., ::-1]
        if mask is not None:
            new_faces = ak.where(mask, new_faces, mesh.faces)
        # if mask is None:
        #     new_faces = mesh.faces[..., ::-1]
        # else:
        #     new_faces = ak.where(mask, ak.mask(mesh.faces, mask)[..., ::-1], mesh.faces)
        mesh['faces'] = new_faces
        self.outputs[0].sv_set(mesh)


register, unregister = bpy.utils.register_classes_factory([SvArrFlipMeshNormalsNode])
