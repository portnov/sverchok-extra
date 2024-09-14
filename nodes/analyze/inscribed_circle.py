# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.inscribed_circle import calc_inscribed_circle
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level

class SvSemiInscribedCircleNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Polygon Inscribed Circle
    Tooltip: Inscribed circle for an arbitrary convex polygon
    """
    bl_idname = 'SvSemiInscribedCircleNode'
    bl_label = 'Polygon Inscribed Circle'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_AREA'
    sv_dependencies = {'scipy'}

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvMatrixSocket', "Center")
        self.outputs.new('SvStringsSocket', "Radius")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        vertices_s = ensure_nesting_level(vertices_s, 4)
        faces_s = self.inputs['Faces'].sv_get()
        faces_s = ensure_nesting_level(faces_s, 4)

        matrix_out = []
        radius_out = []
        for params in zip_long_repeat(vertices_s, faces_s):
            new_matrix = []
            new_radius = []
            for vertices, faces in zip_long_repeat(*params):
                vertices = np.array(vertices)
                print("V", vertices.shape)
                for face in faces:
                    face = np.array(face)
                    circle = calc_inscribed_circle(vertices[face])
                    if circle is not None:
                        new_matrix.append(circle.get_matrix())
                        new_radius.append(circle.radius)
                matrix_out.append(new_matrix)
                radius_out.append(new_radius)

        self.outputs['Center'].sv_set(matrix_out)
        self.outputs['Radius'].sv_set(radius_out)

def register():
    bpy.utils.register_class(SvSemiInscribedCircleNode)

def unregister():
    bpy.utils.unregister_class(SvSemiInscribedCircleNode)

