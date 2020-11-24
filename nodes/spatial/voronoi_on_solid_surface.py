# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import numpy as np
from collections import defaultdict

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
import bmesh
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, throttle_and_update_node, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_bmesh_utils import recalc_normals
from sverchok.utils.voronoi3d import voronoi_on_solid_surface
from sverchok.utils.solid import svmesh_to_solid, SvSolidTopology
from sverchok.utils.surface.freecad import SvSolidFaceSurface
from sverchok.dependencies import scipy, FreeCAD

if scipy is None or FreeCAD is None:
    add_dummy('SvVoronoiOnSolidNode', "Voronoi on Solid Surface", 'scipy and FreeCAD')

if FreeCAD is not None:
    import Part

def mesh_from_faces(fragments):
    verts = [(v.X, v.Y, v.Z) for v in fragments.Vertexes]

    all_fc_verts = {SvSolidTopology.Item(v) : i for i, v in enumerate(fragments.Vertexes)}
    def find_vertex(v):
        #for i, fc_vert in enumerate(fragments.Vertexes):
        #    if v.isSame(fc_vert):
        #        return i
        #return None
        return all_fc_verts[SvSolidTopology.Item(v)]

    edges = []
    for fc_edge in fragments.Edges:
        edge = [find_vertex(v) for v in fc_edge.Vertexes]
        if len(edge) == 2:
            edges.append(edge)

    faces = []
    for fc_face in fragments.Faces:
        incident_verts = defaultdict(set)
        for fc_edge in fc_face.Edges:
            edge = [find_vertex(v) for v in fc_edge.Vertexes]
            if len(edge) == 2:
                i, j = edge
                incident_verts[i].add(j)
                incident_verts[j].add(i)

        face = [find_vertex(v) for v in fc_face.Vertexes]

        vert_idx = face[0]
        correct_face = [vert_idx]

        for i in range(len(face)):
            incident = list(incident_verts[vert_idx])
            other_verts = [i for i in incident if i not in correct_face]
            if not other_verts:
                break
            other_vert_idx = other_verts[0]
            correct_face.append(other_vert_idx)
            vert_idx = other_vert_idx

        if len(correct_face) > 2:
            faces.append(correct_face)

    return verts, edges, faces

class SvVoronoiOnSolidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Voronoi Solid Surface
    Tooltip: Generate Voronoi diagram on the surface of a Solid object
    """
    bl_idname = 'SvVoronoiOnSolidNode'
    bl_label = 'Voronoi on Solid Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    modes = [
            ('RIDGES', "3D Ridges", "Generate ridges of 3D Voronoi diagram", 0),
            ('REGIONS', "3D Regions", "Generate regions of 3D Voronoi diagram", 1),
            ('FACES', "Solid Faces", "Generate Solid Face objects", 2),
            ('MESH', "Mesh", "Generate mesh", 3)
        ]

    thickness : FloatProperty(
        name = "Thickness",
        default = 1.0,
        min = 0.0,
        update=updateNode)

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        update = updateNode)

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['Clipping'].hide_safe = not self.do_clip
        self.outputs['Vertices'].hide_safe = self.mode == 'FACES'
        self.outputs['Edges'].hide_safe = self.mode == 'FACES'
        self.outputs['Faces'].hide_safe = self.mode == 'FACES'
        self.outputs['SolidFaces'].hide_safe = self.mode != 'FACES'

    mode : EnumProperty(
        name = "Mode",
        items = modes,
        update = update_sockets)
    
    do_clip : BoolProperty(
        name = "Clip Box",
        default = True,
        update = update_sockets)

    clip_inner : BoolProperty(
        name = "Clip Inner",
        default = True,
        update = updateNode)

    clip_outer : BoolProperty(
        name = "Clip Outer",
        default = True,
        update = updateNode)

    clipping : FloatProperty(
        name = "Clipping",
        default = 1.0,
        min = 0.0,
        update = updateNode)

    precision : FloatProperty(
        name = "Precision",
        default = 0.0001,
        min = 0.0,
        precision = 4,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', 'Solid')
        self.inputs.new('SvVerticesSocket', "Sites")
        self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', "Clipping").prop_name = 'clipping'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvSurfaceSocket', "SolidFaces")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")
        row = layout.row(align=True)
        row.prop(self, 'clip_inner', toggle=True)
        row.prop(self, 'clip_outer', toggle=True)
        layout.prop(self, 'do_clip', toggle=True)
        if self.mode in {'REGIONS', 'RIDGES'}:
            layout.prop(self, 'normals')
        if self.mode in {'FACES', 'MESH'}:
            layout.prop(self, 'precision')

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        solid_in = self.inputs['Solid'].sv_get()
        sites_in = self.inputs['Sites'].sv_get()
        thickness_in = self.inputs['Thickness'].sv_get()
        clipping_in = self.inputs['Clipping'].sv_get()

        solid_in = ensure_nesting_level(solid_in, 2, data_types=(Part.Shape,))
        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        thickness_in = ensure_nesting_level(thickness_in, 2)
        clipping_in = ensure_nesting_level(clipping_in, 2)

        nested_output = input_level > 1

        verts_out = []
        edges_out = []
        faces_out = []
        fragment_faces_out = []
        for params in zip_long_repeat(solid_in, sites_in, thickness_in, clipping_in):
            new_verts = []
            new_edges = []
            new_faces = []
            new_fragment_faces = []
            for solid, sites, thickness, clipping in zip_long_repeat(*params):
                verts, edges, faces = voronoi_on_solid_surface(solid, sites, thickness,
                            clip_inner = self.clip_inner, clip_outer = self.clip_outer,
                            #skip_added = (self.mode not in {'FACES', 'MESH'}),
                            do_clip=self.do_clip, clipping=clipping,
                            make_regions = (self.mode in {'REGIONS', 'FACES', 'MESH'}))
                if self.mode in {'FACES', 'MESH'} or self.normals:
                    verts, edges, faces = recalc_normals(verts, edges, faces, loop=True)

                if self.mode in {'FACES','MESH'}:
                    fragments = [svmesh_to_solid(vs, fs, self.precision) for vs, fs in zip(verts, faces)]
                    shell = solid.Shells[0]
                    fragments = shell.common(fragments)
                    if self.mode == 'FACES':
                        sv_faces = [SvSolidFaceSurface(f) for f in fragments.Faces]
                        new_fragment_faces.append(sv_faces)
                    else: # MESH
                        verts, edges, faces = mesh_from_faces(fragments)
                        if self.normals:
                            verts, edges, faces = recalc_normals(verts, edges, faces, loop=False)

                new_verts.append(verts)
                new_edges.append(edges)
                new_faces.append(faces)

            if nested_output:
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)
                fragment_faces_out.append(new_fragment_faces)
            else:
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
                fragment_faces_out.extend(new_fragment_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)
        self.outputs['SolidFaces'].sv_set(fragment_faces_out)

def register():
    if scipy is not None and FreeCAD is not None:
        bpy.utils.register_class(SvVoronoiOnSolidNode)

def unregister():
    if scipy is not None and FreeCAD is not None:
        bpy.utils.unregister_class(SvVoronoiOnSolidNode)

