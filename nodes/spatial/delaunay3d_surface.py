# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from itertools import combinations
from math import pi, cos

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
import bmesh
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_mesh_utils import polygons_to_edges, mesh_join
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvDelaunayOnSurfaceNode', "Delaunay 3D", 'scipy')
else:
    from scipy.spatial import Delaunay

class SvDelaunayOnSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Delaunay 3D Surface
    Tooltip: Generate 3D Delaunay Triangulation on a Surface
    """
    bl_idname = 'SvDelaunayOnSurfaceNode'
    bl_label = 'Delaunay on Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    join : BoolProperty(
        name = "Join",
        default = False,
        update = updateNode)

    volume_threshold : FloatProperty(
        name = "PlanarThreshold",
        min = 0,
        default = 1e-4,
        precision = 4,
        update = updateNode)

    edge_threshold : FloatProperty(
        name = "EdgeThreshold",
        min = 0,
        default = 0,
        precision = 4,
        update = updateNode)

    angle_threshold : FloatProperty(
        name = "AngleThreshold",
        min = 0,
        default = 0.02,
        precision = 4,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvVerticesSocket', "UVPoints")
        self.inputs.new('SvStringsSocket', "PlanarThreshold").prop_name = 'volume_threshold'
        self.inputs.new('SvStringsSocket', "EdgeThreshold").prop_name = 'edge_threshold'
        self.inputs.new('SvStringsSocket', "AngleThreshold").prop_name = 'angle_threshold'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def is_planar(self, verts, idxs, threshold):
        if threshold == 0:
            return False
        a, b, c, d = [verts[i] for i in idxs]
        a, b, c, d = np.array(a), np.array(b), np.array(c), np.array(d)
        v1 = b - a
        v2 = c - a
        v3 = d - a
        v1 = v1 / np.linalg.norm(v1)
        v2 = v2 / np.linalg.norm(v2)
        v3 = v3 / np.linalg.norm(v3)
        volume = np.cross(v1, v2).dot(v3) / 6
        return abs(volume) < threshold
    
    def is_too_long(self, verts, edge, threshold):
        if threshold == 0:
            return False
        i, j = edge
        v1, v2 = verts[i], verts[j]
        d = np.linalg.norm(v1 - v2)
        return (d > threshold)

    def is_bad_angle(self, vertices, normals, edge, cos_threshold):
        i,j = edge
        dv = vertices[j] - vertices[i]
        normal1 = normals[i]
        normal2 = normals[j]
        dot1 = np.dot(normal1, dv)
        dot2 = np.dot(normal2, -dv)
        return (abs(dot1) > cos_threshold) or (abs(dot2) > cos_threshold)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_in = self.inputs['Surface'].sv_get()
        uvpoints_in = self.inputs['UVPoints'].sv_get()
        volume_threshold_s = self.inputs['PlanarThreshold'].sv_get()
        edge_threshold_s = self.inputs['EdgeThreshold'].sv_get()
        angle_threshold_s = self.inputs['AngleThreshold'].sv_get()

        input_level = get_data_nesting_level(uvpoints_in)

        surface_in = ensure_nesting_level(surface_in, 2, data_types=(SvSurface,))
        uvpoints_in = ensure_nesting_level(uvpoints_in, 4)
        volume_threshold_s = ensure_nesting_level(volume_threshold_s, 2)
        edge_threshold_s = ensure_nesting_level(edge_threshold_s, 2)
        angle_threshold_s = ensure_nesting_level(angle_threshold_s, 2)

        nested_output = input_level > 3

        verts_out = []
        edges_out = []
        faces_out = []
        for params in zip_long_repeat(surface_in, uvpoints_in, volume_threshold_s, edge_threshold_s, angle_threshold_s):
            verts_item = []
            edges_item = []
            faces_item = set()
            for surface, uvpoints, volume_threshold, edge_threshold, angle_threshold in zip_long_repeat(*params):
                cos_threshold = abs(cos(pi/2 + angle_threshold))
                us = np.array([p[0] for p in uvpoints])
                vs = np.array([p[1] for p in uvpoints])
                vertices = surface.evaluate_array(us, vs)
                normals = surface.normal_array(us, vs)
                tri = Delaunay(vertices)
                verts_item = [vertices.tolist()]
                used_faces = set()
                for simplex_idx, simplex in enumerate(tri.simplices):
                    if self.is_planar(vertices, simplex, volume_threshold):
                        continue
                    faces_count = 0
                    faces = list(combinations(simplex, 3))
                    if any(face in used_faces for face in faces):
                        continue
                    for face in faces:
                        if faces_count <= 2 and not any(self.is_bad_angle(vertices, normals, edge, cos_threshold) or self.is_too_long(vertices, edge, edge_threshold) for edge in combinations(face, 2)):
                            faces_item.add(face)
                            used_faces.add(face)
                            faces_count += 1
                    #verts_item.append(verts_new.tolist())

            if nested_output:
                verts_out.append(verts_item)
                edges_out.append(edges_item)
                faces_out.append([list(faces_item)])
            else:
                verts_out.extend(verts_item)
                edges_out.extend(edges_item)
                faces_out.extend([list(faces_item)])

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvDelaunayOnSurfaceNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvDelaunayOnSurfaceNode)

