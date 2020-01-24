
from sverchok.utils.logging import info, exception

try:
    import scipy
    from scipy.interpolate import Rbf
    scipy_available = True
except ImportError as e:
    info("SciPy is not available, Bend Along Minimal Surface node will not be available")
    scipy_available = False

import numpy as np
from math import sqrt

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, ensure_nesting_level
from sverchok.utils.geom import diameter

from sverchok_extra.data.surface import SvExRbfSurface

if scipy_available:

    class SvExBendAlongMinSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Bend minimal surface
        Tooltip: Bend object along minimal surface
        """
        bl_idname = 'SvExBendAlongMinSurfaceNode'
        bl_label = 'Bend Along Minimal Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'

        axes = [
                ("X", "X", "X axis", 1),
                ("Y", "Y", "Y axis", 2),
                ("Z", "Z", "Z axis", 3)
            ]

        orient_axis_: EnumProperty(
            name="Orientation axis", description="Which axis of object to put along path",
            default="Z", items=axes, update=updateNode)

        def get_axis_idx(self, letter):
            return 'XYZ'.index(letter)

        def get_orient_axis_idx(self):
            return self.get_axis_idx(self.orient_axis_)
    
        orient_axis = property(get_orient_axis_idx)

        autoscale: BoolProperty(
            name="Auto scale", description="Scale object along orientation axis automatically",
            default=False, update=updateNode)

        flip: BoolProperty(
            name="Flip surface",
            description="Flip the surface orientation",
            default=False, update=updateNode)

        normal_delta : FloatProperty(
            name = "Normal delta",
            description = "Controls the normal calculation precision",
            default = 1e-4, min = 1e-6,
            precision = 4,
            update = updateNode)

        coord_modes = [
            ('XY', "X Y -> Z", "XY -> Z function", 0),
            ('UV', "U V -> X Y Z", "UV -> XYZ function", 1)
        ]

        coord_mode : EnumProperty(
            name = "Coordinates",
            items = coord_modes,
            default = 'XY',
            update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'
            self.inputs.new('SvVerticesSocket', 'Vertices')
            self.outputs.new('SvVerticesSocket', 'Vertices')

        def draw_buttons(self, context, layout):
            layout.label(text="Surface mode:")
            layout.prop(self, "coord_mode", expand=True)
            layout.label(text="Object vertical axis:")
            layout.prop(self, "orient_axis_", expand=True)
            layout.prop(self, "autoscale", toggle=True)

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            layout.prop(self, 'flip')
            layout.prop(self, 'normal_delta')

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
            us = np.array([vertex[u_index] for vertex in vertices])
            vs = np.array([vertex[v_index] for vertex in vertices])
            min_u = us.min()
            max_u = us.max()
            min_v = vs.min()
            max_v = vs.max()

            size_u = max_u - min_u
            size_v = max_v - min_v

            if size_u < 0.00001:
                raise Exception("Object has too small size in U direction")
            if size_v < 0.00001:
                raise Exception("Object has too small size in V direction")

            result_us = (us - min_u) / size_u
            result_vs = (vs - min_v) / size_v

            return us, vs # result_us, result_vs

        def calc_normals(self, surface, us, vs, surf_vertices):
            u_plus = self.evaluate(surface, us + self.normal_delta, vs)
            v_plus = self.evaluate(surface, us, vs + self.normal_delta)
            du = u_plus - surf_vertices
            dv = v_plus - surf_vertices
            #self.info("Du: %s", du)
            #self.info("Dv: %s", dv)
            normal = np.cross(du, dv)
            norm = np.linalg.norm(normal, axis=1)[np.newaxis].T
            #if norm != 0:
            normal = normal / norm
            #self.info("Normals: %s", normal)
            return normal

        def build_output(self, surface, XI, YI, ZI):
            if surface.input_orientation == 'X':
                YI, ZI, XI = XI, YI, ZI
            elif surface.input_orientation == 'Y':
                ZI, XI, YI = XI, YI, ZI
            else: # Z
                pass
            verts = np.dstack((XI, YI, ZI))
            if surface.has_matrix:
                verts = verts - surface.input_matrix.translation
                np_matrix = np.array(surface.input_matrix.to_3x3())
                verts = np.apply_along_axis(lambda v : np_matrix @ v, 2, verts)
            return verts

        def evaluate(self, surface, us, vs):
            surf_vertices = np.array( surface.rbf(us, vs) )
            if self.coord_mode == 'XY':
                surf_vertices = np.dstack((us, vs, surf_vertices))[0]
            return surf_vertices 

        def bend(self, surface, vertices, us, vs):
            if self.autoscale:
                u_index, v_index = self.get_other_axes()
                scale_u = diameter(vertices, u_index) / surface.u_size
                scale_v = diameter(vertices, v_index) / surface.v_size
                scale_z = sqrt(scale_u * scale_v)
                #self.info("Scale Z: %s", scale_z)
            else:
                scale_z = 1.0
            if self.flip:
                scale_z = - scale_z

            #self.info("Us: %s", us)
            #self.info("Vs: %s", vs)
            surf_vertices = self.evaluate(surface, us, vs)
            spline_normals = np.array( self.calc_normals(surface, us, vs, surf_vertices) )
            zs = np.array( [src_vertex[self.orient_axis] for src_vertex in vertices] )
            zs = zs[np.newaxis].T
            new_vertices = surf_vertices + scale_z * zs * spline_normals
            return new_vertices

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return
            if not self.inputs['Vertices'].is_linked:
                return

            surfaces_s = self.inputs['Surface'].sv_get()
            vertices_s = self.inputs['Vertices'].sv_get()

            verts_out = []
            for surface, vertices in zip_long_repeat(surfaces_s, vertices_s):
                if surface.coord_mode != self.coord_mode:
                    self.warning("Input surface mode is %s, but Evaluate node mode is %s; the result can be unexpected", surface.coord_mode, self.coord_mode)

                us, vs = self.get_uv(vertices)
                new_vertices = self.bend(surface, vertices, us, vs)
#                 if self.coord_mode == 'XY':
#                     new_vertices = self.build_output(surface, us, vs, new_vertices)
#                     new_vertices = new_vertices.tolist()
#                     new_vertices = sum(new_vertices, [])
#                 else:
                new_vertices = new_vertices.tolist()
                verts_out.append(new_vertices)

            self.outputs['Vertices'].sv_set(verts_out)

def register():
    if scipy_available:
        bpy.utils.register_class(SvExBendAlongMinSurfaceNode)

def unregister():
    if scipy_available:
        bpy.utils.unregister_class(SvExBendAlongMinSurfaceNode)

