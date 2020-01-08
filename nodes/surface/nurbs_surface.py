
from sverchok.utils.logging import info, exception

try:
    from geomdl import NURBS
    from geomdl import tessellate
    from geomdl import knotvector
    geomdl_available = True
except ImportError as e:
    info("geomdl package is not available, NURBS Surface node will not be available")
    geomdl_available = False

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList

if geomdl_available:
    
    class SvExNurbsSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: NURBS Surface
        Tooltip: NURBS Surface
        """
        bl_idname = 'SvExNurbsSurfaceNode'
        bl_label = 'NURBS Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'

        sample_size : FloatProperty(
                name = "Samples",
                default = 50,
                min = 4,
                update = updateNode)

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

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "ControlPoints")
            self.inputs.new('SvStringsSocket', "Weights")
            self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
            self.inputs.new('SvStringsSocket', "USize").prop_name = 'u_size'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Faces")

        def draw_buttons(self, context, layout):
            layout.prop(self, "input_mode")

        def process(self):
            vertices_s = self.inputs['ControlPoints'].sv_get()
            has_weights = self.inputs['Weights'].is_linked
            weights_s = self.inputs['Weights'].sv_get(default = [[1.0]])
            samples_s = self.inputs['Samples'].sv_get()
            u_size_s = self.inputs['USize'].sv_get()
            
            def convert_row(verts_row, weights_row):
                return [(x, y, z, w) for (x,y,z), w in zip(verts_row, weights_row)]

            verts_out = []
            edges_out = []
            faces_out = []
            for vertices, weights, samples, u_size in zip_long_repeat(vertices_s, weights_s, samples_s, u_size_s):
                if isinstance(samples, (list, tuple)):
                    samples = samples[0]
                if isinstance(u_size, (list, tuple)):
                    u_size = u_size[0]
                if self.input_mode == '1D':
                    fullList(weights, len(vertices))
                else:
                    for verts_u, weights_u in vertices:
                        fullList(weights_u, len(verts_u))

                # Generate surface
                surf = NURBS.Surface()
                surf.degree_u = 3
                surf.degree_v = 3

                if self.input_mode == '1D':
                    # Control points
                    n_u = u_size
                    n_v = len(vertices) // n_u
                    surf.ctrlpts_size_u = n_u
                    surf.ctrlpts_size_v = n_v
                    surf.ctrlpts = vertices
                    surf.weights = weights
                else:
                    # Control points
                    surf.ctrlpts2d = list(map(convert_row, vertices, weights))
                    n_u = len(verts_in)
                    n_v = len(verts_in[0])

                surf.knotvector_u = knotvector.generate(surf.degree_u, n_u)
                surf.knotvector_v = knotvector.generate(surf.degree_v, n_v)

                surf.sample_size = samples

                surf.tessellate()
                new_verts = [vert.data for vert in surf.vertices]
                new_faces = [f.data for f in surf.faces]
                verts_out.append(new_verts)
                faces_out.append(new_faces)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Faces'].sv_set(faces_out)

def register():
    if geomdl_available:
        bpy.utils.register_class(SvExNurbsSurfaceNode)

def unregister():
    if geomdl_available:
        bpy.utils.unregister_class(SvExNurbsSurfaceNode)

