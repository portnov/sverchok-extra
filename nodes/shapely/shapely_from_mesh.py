# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely
from sverchok_extra.utils.shapely import from_mesh

class SvExShapelyFromMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Mesh
    Tooltip: 2D Mesh
    """
    bl_idname = "SvExShapelyFromMeshNode"
    bl_label = "Mesh to 2D Geometry"
    sv_icon = 'SV_NGON'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_dependencies = {'shapely'}

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_s = self.inputs['Vertices'].sv_get()
        input_level = get_data_nesting_level(verts_s)
        flat_output = input_level == 3
        verts_s = ensure_nesting_level(verts_s, 4)
        edges_s = self.inputs['Edges'].sv_get()
        edges_s = ensure_nesting_level(edges_s, 4)
        faces_s = self.inputs['Faces'].sv_get()
        faces_s = ensure_nesting_level(faces_s, 4)

        geometry_out = []
        for params in zip_long_repeat(verts_s, edges_s, faces_s):
            new_geometry = []
            for verts, edges, faces in zip_long_repeat(*params):
                g = from_mesh(verts, edges, faces)
                new_geometry.append(g)
            if flat_output:
                geometry_out.extend(new_geometry)
            else:
                geometry_out.append(new_geometry)
        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelyFromMeshNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyFromMeshNode)

