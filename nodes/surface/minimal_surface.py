
from sverchok.utils.logging import info, exception

try:
    import scipy
    from scipy.interpolate import Rbf
    scipy_available = True
except ImportError as e:
    info("SciPy is not available, MinimalSurface node will not be available")
    scipy_available = False

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

if scipy_available:
    class SvExMinimalSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Minimal Surface
        Tooltip: Minimal Surface
        """
        bl_idname = 'SvExMinimalSurfaceNode'
        bl_label = 'Minimal Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'

        @throttled
        def update_sockets(self, context):
            self.inputs['Matrix'].hide_safe = self.coord_mode == 'UV'

        coord_modes = [
            ('XY', "X Y Z", "XY -> Z function", 0),
            ('UV', "U V", "UV -> XYZ function", 1)
        ]

        coord_mode : EnumProperty(
            name = "Coordinates",
            items = coord_modes,
            default = 'XY',
            update = update_sockets)

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

        axes = [
            ('X', "X", "X axis", 0),
            ('Y', "Y", "Y axis", 1),
            ('Z', "Z", "Z axis", 2)
        ]

        orientation : EnumProperty(
                name = "Orientation",
                items = axes,
                default = 'Z',
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
            self.inputs.new('SvMatrixSocket', "Matrix")
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvStringsSocket', "Faces")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.prop(self, "coord_mode", expand=True)
            layout.prop(self, "function")
            if self.coord_mode == 'XY':
                layout.prop(self, "orientation", expand=True)

        def make_edges_xy(self, n_points):
            edges = []
            for row in range(n_points):
                e_row = [(i + n_points * row, (i+1) + n_points * row) for i in range(n_points-1)]
                edges.extend(e_row)
                if row < n_points - 1:
                    e_col = [(i + n_points * row, i + n_points * (row+1)) for i in range(n_points)]
                    edges.extend(e_col)
            return edges

        def make_faces_xy(self, n_points):
            faces = []
            for row in range(n_points - 1):
                for col in range(n_points - 1):
                    i = row + col * n_points
                    face = (i, i+n_points, i+n_points+1, i+1)
                    faces.append(face)
            return faces

        def make_uv(self, vertices):

            def distance(v1, v2):
                v1 = np.array(v1)
                v2 = np.array(v2)
                return np.linalg.norm(v1-v2)

            u = 0
            v = 0
            us, vs = [], []
            prev_row = None
            rev_vs = None
            for row in vertices:
                u = 0
                row_vs = []
                prev_vertex = None
                for j, vertex in enumerate(row):
                    if prev_row is not None:
                        dv = distance(prev_row[j], vertex)
                        v = prev_vs[j] + dv
                    if prev_vertex is not None:
                        du = distance(prev_vertex, vertex)
                        u += du
                    us.append(u)
                    vs.append(v)
                    row_vs.append(v)
                    prev_vertex = vertex
                prev_row = row
                prev_vs = row_vs

            return np.array(us), np.array(vs)

        def process(self):

            if not self.inputs['Vertices'].is_linked:
                return

            if not self.outputs['Vertices'].is_linked:
                return

            vertices_s = self.inputs['Vertices'].sv_get()
            if self.coord_mode == 'UV':
                vertices_s = ensure_nesting_level(vertices_s, 4)
            points_s = self.inputs['GridPoints'].sv_get()
            epsilon_s = self.inputs['Epsilon'].sv_get()
            smooth_s = self.inputs['Smooth'].sv_get()
            matrices_s = self.inputs['Matrix'].sv_get(default = [[Matrix()]])

            verts_out = []
            edges_out = []
            faces_out = []
            for vertices, matrix, grid_points, epsilon, smooth in zip_long_repeat(vertices_s, matrices_s, points_s, epsilon_s, smooth_s):
                if isinstance(epsilon, (list, int)):
                    epsilon = epsilon[0]
                if isinstance(smooth, (list, int)):
                    smooth = smooth[0]
                if isinstance(grid_points, (list, int)):
                    grid_points = grid_points[0]
                if isinstance(matrix, list):
                    matrix = matrix[0]
                has_matrix = self.coord_mode == 'XY' and matrix is not None and matrix != Matrix()

                if self.coord_mode == 'XY':
                    XYZ = np.array(vertices)
                else: # UV
                    all_vertices = sum(vertices, [])
                    XYZ = np.array(all_vertices)
                if has_matrix:
                    np_matrix = np.array(matrix.to_3x3())
                    inv_matrix = np.linalg.inv(np_matrix)
                    #print(matrix)
                    #print(XYZ)
                    translation = np.array(matrix.translation)
                    XYZ = np.matmul(inv_matrix, XYZ.T).T + translation

                if self.coord_mode == 'XY':
                    if self.orientation == 'X':
                        reorder = np.array([1, 2, 0])
                        XYZ = XYZ[:, reorder]
                    elif self.orientation == 'Y':
                        reorder = np.array([2, 0, 1])
                        XYZ = XYZ[:, reorder]
                    else: # Z
                        pass

                if self.coord_mode == 'XY':
                    x_min = XYZ[:,0].min()
                    x_max = XYZ[:,0].max()
                    y_min = XYZ[:,1].min()
                    y_max = XYZ[:,1].max()
                    xi = np.linspace(x_min, x_max, grid_points)
                    yi = np.linspace(y_min, y_max, grid_points)
                    XI, YI = np.meshgrid(xi, yi)

                    rbf = Rbf(XYZ[:,0],XYZ[:,1],XYZ[:,2],function=self.function,smooth=smooth,epsilon=epsilon)
                    ZI = rbf(XI,YI)

                    if self.orientation == 'X':
                        YI, ZI, XI = XI, YI, ZI
                    elif self.orientation == 'Y':
                        ZI, XI, YI = XI, YI, ZI
                    else: # Z
                        pass

                    new_verts = np.dstack((XI,YI,ZI))
                else:
                    us, vs = self.make_uv(vertices)
                    US, VS = np.meshgrid(us, vs)

                    rbf = Rbf(us, vs, all_vertices,
                            function = self.function,
                            smooth = smooth,
                            epsilon = epsilon, mode='N-D')

                    u_min = us.min()
                    v_min = vs.min()
                    u_max = us.max()
                    v_max = vs.max()
                    target_us = np.linspace(u_min, u_max, grid_points)
                    target_vs = np.linspace(v_min, v_max, grid_points)
                    target_US, target_VS = np.meshgrid(target_us, target_vs)
                    new_verts = rbf(target_US, target_VS)

                if has_matrix:
                    new_verts = new_verts - translation
                    new_verts = np.apply_along_axis(lambda v : np_matrix @ v, 2, new_verts)
                new_verts = new_verts.tolist()
                all_new_verts = sum(new_verts, [])
                new_edges = self.make_edges_xy(grid_points)
                new_faces = self.make_faces_xy(grid_points)

                verts_out.append(all_new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Faces'].sv_set(faces_out)

def register():
    if scipy_available:
        bpy.utils.register_class(SvExMinimalSurfaceNode)

def unregister():
    if scipy_available:
        bpy.utils.unregister_class(SvExMinimalSurfaceNode)

