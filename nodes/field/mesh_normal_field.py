
import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.logging import info, exception
from sverchok_extra.data import SvExBvhAttractorVectorField

class SvExMeshNormalFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Mesh Normal Field
    Tooltip: Generate vector field by mesh normal at the nearest point
    """
    bl_idname = 'SvExMeshNormalFieldNode'
    bl_label = 'Mesh Nearest Normal'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvExVectorFieldSocket', "Field").display_shape = 'CIRCLE_DOT'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        faces_s = self.inputs['Faces'].sv_get()

        fields_out = []
        for vertices, faces in zip_long_repeat(vertices_s, faces_s):
            field = SvExBvhAttractorVectorField(verts=vertices, faces=faces, use_normal=True)
            fields_out.append(field)
        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvExMeshNormalFieldNode)

def unregister():
    bpy.utils.unregister_class(SvExMeshNormalFieldNode)

