
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, fullList
from sverchok.utils.logging import info, exception

from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.interpolate import SmoothBivariateSpline

    class SvExBivariateSplineNode(SverchCustomTreeNode, bpy.types.Node):
        """
        Triggers: Smooth Bivariate Spline Surface
        Tooltip: Smooth weighted surface spline
        """
        bl_idname = 'SvExBivariateSplineNode'
        bl_label = 'Smooth Weighted Surface Spline'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EX_BVSPLINE'

        grid_points : IntProperty(
                name = "Points",
                default = 25,
                min = 3,
                update = updateNode)

        smooth : FloatProperty(
                name = "Smooth",
                default = 1.0,
                min = 0.0,
                update = updateNode)

        degree : IntProperty(
                name = "Degree",
                default = 3,
                min = 2, max = 4,
                update = updateNode)

        axes = [
            ('X', "X axis", "X axis", 0),
            ('Y', "Y axis", "Y axis", 1),
            ('Z', "Z axis", "Z axis", 2)
        ]

        orientation : EnumProperty(
                name = "Orientation",
                items = axes,
                default = 'Z',
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.inputs.new('SvStringsSocket', "GridPoints").prop_name = 'grid_points'
            self.inputs.new('SvStringsSocket', "Weights")
            self.inputs.new('SvStringsSocket', "Smooth").prop_name = 'smooth'
            self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
            self.inputs.new('SvMatrixSocket', "Matrix")
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvStringsSocket', "Faces")

        def draw_buttons(self, context, layout):
            layout.prop(self, "orientation", expand=True)

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
            smooth_s = self.inputs['Smooth'].sv_get()
            degree_s = self.inputs['Degree'].sv_get()
            weights_s = self.inputs['Weights'].sv_get(default = [[1.0]])
            matrices_s = self.inputs['Matrix'].sv_get(default = [[Matrix()]])

            verts_out = []
            edges_out = []
            faces_out = []
            for vertices, weights, degree, matrix, smooth, grid_points in zip_long_repeat(vertices_s, weights_s, degree_s, matrices_s, smooth_s, points_s):
                if isinstance(grid_points, (list, tuple)):
                    grid_points = grid_points[0]
                if isinstance(degree, (list, tuple)):
                    degree = degree[0]
                if isinstance(smooth, (list, tuple)):
                    smooth = smooth[0]
                if isinstance(matrix, list):
                    matrix = matrix[0]
                has_matrix = matrix is not None and matrix != Matrix()

                fullList(weights, len(vertices))

                smooth = smooth * len(vertices)

                XYZ = np.array(vertices)
                if has_matrix:
                    np_matrix = np.array(matrix.to_3x3())
                    inv_matrix = np.linalg.inv(np_matrix)
                    #print(matrix)
                    #print(XYZ)
                    translation = np.array(matrix.translation)
                    XYZ = np.matmul(inv_matrix, XYZ.T).T + translation
                if self.orientation == 'X':
                    reorder = np.array([1, 2, 0])
                    XYZ = XYZ[:, reorder]
                elif self.orientation == 'Y':
                    reorder = np.array([2, 0, 1])
                    XYZ = XYZ[:, reorder]
                else: # Z
                    pass

                x_min = XYZ[:,0].min()
                x_max = XYZ[:,0].max()
                y_min = XYZ[:,1].min()
                y_max = XYZ[:,1].max()
                xi = np.linspace(x_min, x_max, grid_points)
                yi = np.linspace(y_min, y_max, grid_points)
                XI, YI = np.meshgrid(xi, yi)

                spline = SmoothBivariateSpline(XYZ[:,0], XYZ[:,1], XYZ[:,2],
                            kx = degree, ky = degree,
                            w=weights,
                            s=smooth)
                ZI = spline(xi, yi)

                if self.orientation == 'X':
                    YI, ZI, XI = XI, YI, ZI
                elif self.orientation == 'Y':
                    ZI, XI, YI = XI, YI, ZI
                else: # Z
                    pass

                new_verts = np.dstack((YI,XI,ZI))
                if has_matrix:
                    new_verts = new_verts - translation
                    new_verts = np.apply_along_axis(lambda v : np_matrix @ v, 2, new_verts)
                new_verts = new_verts.tolist()
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
    if scipy is not None:
        bpy.utils.register_class(SvExBivariateSplineNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExBivariateSplineNode)

