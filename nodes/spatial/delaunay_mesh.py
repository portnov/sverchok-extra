# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from collections import defaultdict

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat, repeat_last_for_length, updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.mesh_spatial import mesh_insert_verts, find_nearest_idxs

class SvDelaunayOnMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Delaunay Mesh
    Tooltip: Add vertices to the mesh by use of Delaunay triangulation
    """
    bl_idname = 'SvDelaunayOnMeshNode'
    bl_label = 'Delaunay on Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    exclude_boundary : BoolProperty(
        name = "Exclude edges",
        description = "Avoid adding vertices too near to existing edges",
        default = True,
        update = updateNode)

    recalc_normals : BoolProperty(
        name = "Correct normals",
        default = True,
        update = updateNode)

    preserve_shape : BoolProperty(
        name = "Preserve shape",
        default = True,
        update = updateNode)

    def update_sockets(self, context):
        self.inputs['FaceIndex'].hide_safe = self.mode != 'INDEX'
        updateNode(self, context)

    modes = [
            ('INDEX', "By face index", "Specify index of the face for each vertex being added", 0),
            ('NEAREST', "Nearest", "Use nearest face", 1)
        ]

    mode : EnumProperty(
            name = "Project",
            description = "How to define which vertex should be added to which face",
            items = modes,
            default = 'INDEX',
            update = update_sockets)

    accuracy : IntProperty(
            name = "Accuracy",
            default = 4,
            min = 1,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')
        layout.prop(self, 'exclude_boundary')
        layout.prop(self, 'preserve_shape')
        layout.prop(self, 'recalc_normals')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvVerticesSocket', 'AddVerts')
        self.inputs.new('SvStringsSocket', 'FaceIndex')
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['Vertices'].sv_get()
        faces_in = self.inputs['Faces'].sv_get()
        add_verts_in = self.inputs['AddVerts'].sv_get()
        if self.mode == 'INDEX':
            face_idxs_in = self.inputs['FaceIndex'].sv_get()
        else:
            face_idxs_in = [[[]]]


        tolerance = 10**(-self.accuracy)

        verts_out = []
        edges_out = []
        faces_out = []
        for verts, faces, add_verts, face_idxs in zip_long_repeat(verts_in, faces_in, add_verts_in, face_idxs_in):
            if self.mode == 'INDEX':
                face_idxs = repeat_last_for_length(face_idxs, len(add_verts))
            else:
                face_idxs = find_nearest_idxs(verts, faces, add_verts)

            add_verts_by_face = defaultdict(list)
            for add_vert, idx in zip(add_verts, face_idxs):
                add_verts_by_face[idx].append(add_vert)

            new_verts, new_edges, new_faces = mesh_insert_verts(verts, faces, add_verts_by_face,
                                                epsilon = tolerance,
                                                exclude_boundary = self.exclude_boundary,
                                                preserve_shape = self.preserve_shape,
                                                recalc_normals = self.recalc_normals)

            verts_out.append(new_verts)
            edges_out.append(new_edges)
            faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvDelaunayOnMeshNode)

def unregister():
    bpy.utils.unregister_class(SvDelaunayOnMeshNode)

