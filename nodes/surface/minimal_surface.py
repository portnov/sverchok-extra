
import scipy
from scipy.interpolate import Rbf
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat

class SvExMinimalSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Minimal Surface
    Tooltip: Minimal Surface
    """
    bl_idname = 'SvExMinimalSurfaceNode'
    bl_label = 'Minimal Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    functions = [
        ('multiquadric', "Multi Quadric", "Multi Quadric", 0),
        ('inverse', "Inverse", "Inverse", 1),
        ('gaussian', "Gaussian", "Gaussian", 2),
        ('cubic', "Cubic", "Cubic", 3),
        ('quintic', "Quintic", "Qunitic", 4),
        ('thin_plate', "Thin Plate", "Thin Plate", 5)
    ]

    function : EnumProperty(
            name = "Function",
            items = functions,
            default = 'multiquadric',
            update = updateNode)

    grid_points : IntProperty(
            name = "Points",
            default = 25,
            min = 3,
            update = updateNode)

    epsilon : FloatProperty(
            name = "Epsilon",
            default = 1.0,
            min = 0.0,
            update = updateNode)
    
    smooth : FloatProperty(
            name = "Smooth",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "GridPoints").prop_name = 'grid_points'
        self.inputs.new('SvStringsSocket', "Epsilon").prop_name = 'epsilon'
        self.inputs.new('SvStringsSocket', "Smooth").prop_name = 'smooth'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def draw_buttons(self, context, layout):
        layout.prop(self, "function")

    def make_edges(self, n_points):
        edges = []
        for row in range(n_points):
            e_row = [(i + n_points * row, (i+1) + n_points * row) for i in range(n_points-1)]
            edges.extend(e_row)
            if row < n_points - 1:
                e_col = [(i + n_points * row, i + n_points * (row+1)) for i in range(n_points)]
                edges.extend(e_col)
        return edges

    def make_faces(self, n_points):
        faces = []
        for row in range(n_points - 1):
            for col in range(n_points - 1):
                i = row + col * n_points
                face = (i, i+n_points, i+n_points+1, i+1)
                faces.append(face)
        return faces

    def process(self):

        if not self.inputs['Vertices'].is_linked:
            return

        if not self.outputs['Vertices'].is_linked:
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        points_s = self.inputs['GridPoints'].sv_get()
        epsilon_s = self.inputs['Epsilon'].sv_get()
        smooth_s = self.inputs['Smooth'].sv_get()

        verts_out = []
        edges_out = []
        faces_out = []
        for vertices, grid_points, epsilon, smooth in zip_long_repeat(vertices_s, points_s, epsilon_s, smooth_s):
            if isinstance(epsilon, (list, int)):
                epsilon = epsilon[0]
            if isinstance(smooth, (list, int)):
                smooth = smooth[0]
            if isinstance(grid_points, (list, int)):
                grid_points = grid_points[0]

            XYZ = np.array(vertices)
            x_min = XYZ[:,0].min()
            x_max = XYZ[:,0].max()
            y_min = XYZ[:,1].min()
            y_max = XYZ[:,1].max()
            xi = np.linspace(x_min, x_max, grid_points)
            yi = np.linspace(y_min, y_max, grid_points)
            XI, YI = np.meshgrid(xi, yi)

            rbf = Rbf(XYZ[:,0],XYZ[:,1],XYZ[:,2],function=self.function,smooth=smooth,epsilon=epsilon)
            ZI = rbf(XI,YI)

            new_verts = np.dstack((XI,YI,ZI)).tolist()
            new_verts = sum(new_verts, [])
            new_edges = self.make_edges(grid_points)
            new_faces = self.make_faces(grid_points)
            verts_out.append(new_verts)
            edges_out.append(new_edges)
            faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvExMinimalSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExMinimalSurfaceNode)

