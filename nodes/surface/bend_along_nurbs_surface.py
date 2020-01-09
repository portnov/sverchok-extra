
from sverchok.utils.logging import info, exception

try:
    from geomdl import NURBS
    from geomdl import tessellate
    from geomdl import knotvector
    from geomdl import operations
    geomdl_available = True
except ImportError as e:
    info("geomdl package is not available, NURBS Surface node will not be available")
    geomdl_available = False

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, ensure_nesting_level

if geomdl_available:
    
    class SvExBendAlongNurbsSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Bend NURBS Surface
        Tooltip: Bend object along NURBS Surface
        """
        bl_idname = 'SvExBendAlongNurbsSurfaceNode'
        bl_label = 'Bend Along NURBS Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'

        axes = [
                ("X", "X", "X axis", 1),
                ("Y", "Y", "Y axis", 2),
                ("Z", "Z", "Z axis", 3)
            ]

        orient_axis_: EnumProperty(
            name="Orientation axis", description="Which axis of object to put along path",
            default="Z", items=axes, update=updateNode)

        input_modes = [
                ('1D', "Single list", "List of all control points (concatenated)", 1),
                ('2D', "Separated lists", "List of lists of control points", 2)
            ]

        @throttled
        def update_sockets(self, context):
            self.inputs['USize'].hide_safe = self.input_mode == '2D'

        input_mode : EnumProperty(
                name = "Input mode",
                default = '1D',
                items = input_modes,
                update = update_sockets)

        u_size : IntProperty(
                name = "U Size",
                default = 5,
                min = 3,
                update = updateNode)

        sample_size : IntProperty(
                name = "Samples",
                default = 50,
                min = 4,
                update = updateNode)

        def get_axis_idx(self, letter):
            return 'XYZ'.index(letter)

        def get_orient_axis_idx(self):
            return self.get_axis_idx(self.orient_axis_)
    
        orient_axis = property(get_orient_axis_idx)

        autoscale: BoolProperty(
            name="Auto scale", description="Scale object along orientation axis automatically",
            default=False, update=updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "ControlPoints")
            self.inputs.new('SvStringsSocket', "Weights")
            self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
            self.inputs.new('SvStringsSocket', "USize").prop_name = 'u_size'
            self.inputs.new('SvVerticesSocket', 'Vertices')
            self.outputs.new('SvVerticesSocket', 'Vertices')

        def draw_buttons(self, context, layout):
            layout.prop(self, "input_mode")
            layout.prop(self, "orient_axis_", expand=True)

        def get_other_axes(self):
            # Select U and V to be two axes except orient_axis
            if self.orient_axis_ == 'X':
                u_index, v_index = 1,2
            elif self.orient_axis_ == 'Y':
                u_index, v_index = 2,0
            else:
                u_index, v_index = 0,1
            return u_index, v_index
        
        def get_uv(self, vertices):
            """
            Translate source vertices to UV space of future spline.
            vertices must be list of list of 3-tuples.
            """
            #print("Vertices: {} of {} of {}".format(type(vertices), type(vertices[0]), type(vertices[0][0])))
            u_index, v_index = self.get_other_axes()

            # Rescale U and V coordinates to [0, 1], drop third coordinate
            us = [vertex[u_index] for col in vertices for vertex in col]
            vs = [vertex[v_index] for col in vertices for vertex in col]
            min_u = min(us)
            max_u = max(us)
            min_v = min(vs)
            max_v = max(vs)

            size_u = max_u - min_u
            size_v = max_v - min_v

            if size_u < 0.00001:
                raise Exception("Object has too small size in U direction")
            if size_v < 0.00001:
                raise Exception("Object has too small size in V direction")
            result = [[((vertex[u_index] - min_u)/size_u, (vertex[v_index] - min_v)/size_v) for vertex in col] for col in vertices]

            return size_u, size_v, result

        def evaluate(self, surf, vertices):
            src_size_u, src_size_v, uv_coords = self.get_uv(vertices)
            new_vertices = []
            for uv_row, vertices_row in zip(uv_coords, vertices):
                new_row = []
                surf_vertices = np.array( surf.evaluate_list(uv_row) )
                spline_normals = np.array( operations.normal(surf, uv_row) )[:,1,:]
                zs = np.array( [src_vertex[self.orient_axis] for src_vertex in vertices_row] )
                zs = zs[np.newaxis].T
                new_row = surf_vertices + zs * spline_normals
                new_vertices.extend(new_row.tolist())
            return new_vertices

        def process(self):
            control_points_s = self.inputs['ControlPoints'].sv_get()
            has_weights = self.inputs['Weights'].is_linked
            weights_s = self.inputs['Weights'].sv_get(default = [[1.0]])
            samples_s = self.inputs['Samples'].sv_get()
            u_size_s = self.inputs['USize'].sv_get()
            vertices_s = self.inputs['Vertices'].sv_get()
            vertices_s = ensure_nesting_level(vertices_s, 4)

            def convert_row(verts_row, weights_row):
                return [(x, y, z, w) for (x,y,z), w in zip(verts_row, weights_row)]

            verts_out = []
            for control_points, weights, vertices, samples, u_size in zip_long_repeat(control_points_s, weights_s, vertices_s, samples_s, u_size_s):
                if isinstance(samples, (list, tuple)):
                    samples = samples[0]
                if isinstance(u_size, (list, tuple)):
                    u_size = u_size[0]
                if self.input_mode == '1D':
                    fullList(weights, len(control_points))
                else:
                    for verts_u, weights_u in control_points:
                        fullList(weights_u, len(verts_u))

                # Generate surface
                surf = NURBS.Surface()
                surf.degree_u = 3
                surf.degree_v = 3

                if self.input_mode == '1D':
                    # Control points
                    n_u = u_size
                    n_v = len(control_points) // n_u
                    surf.ctrlpts_size_u = n_u
                    surf.ctrlpts_size_v = n_v
                    surf.ctrlpts = control_points
                    surf.weights = weights
                else:
                    # Control points
                    surf.ctrlpts2d = list(map(convert_row, control_points, weights))
                    n_u = len(verts_in)
                    n_v = len(verts_in[0])

                surf.knotvector_u = knotvector.generate(surf.degree_u, n_u)
                surf.knotvector_v = knotvector.generate(surf.degree_v, n_v)

                surf.sample_size = samples

                surf.evaluate()

                new_vertices = self.evaluate(surf, vertices)
                verts_out.append(new_vertices)

            self.outputs['Vertices'].sv_set(verts_out)

def register():
    if geomdl_available:
        bpy.utils.register_class(SvExBendAlongNurbsSurfaceNode)

def unregister():
    if geomdl_available:
        bpy.utils.unregister_class(SvExBendAlongNurbsSurfaceNode)


