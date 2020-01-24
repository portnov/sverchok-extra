
from sverchok.utils.logging import info, exception

try:
    from geomdl import NURBS, BSpline
    from geomdl import tessellate
    from geomdl import knotvector
    from geomdl import operations
    geomdl_available = True
except ImportError as e:
    info("geomdl package is not available, NURBS Surface node will not be available")
    geomdl_available = False

import numpy as np
from math import sqrt

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, ensure_nesting_level
from sverchok.utils.geom import diameter

if geomdl_available:
    
    class SvExBendAlongGeomdlSurface(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Bend NURBS / Bezier Surface
        Tooltip: Bend object along NURBS Surface
        """
        bl_idname = 'SvExBendAlongGeomdlSurface'
        bl_label = 'Bend Along NURBS Surface'
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

        def sv_init(self, context):
            self.inputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'
            self.inputs.new('SvVerticesSocket', 'Vertices')
            self.outputs.new('SvVerticesSocket', 'Vertices')

        def draw_buttons(self, context, layout):
            layout.label(text="Object vertical axis:")
            layout.prop(self, "orient_axis_", expand=True)
            layout.prop(self, "autoscale", toggle=True)

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            layout.prop(self, 'flip')

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
            us = [vertex[u_index] for vertex in vertices]
            vs = [vertex[v_index] for vertex in vertices]
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
            result = [((vertex[u_index] - min_u)/size_u, (vertex[v_index] - min_v)/size_v) for vertex in vertices]

            return size_u, size_v, result

        def evaluate(self, surf, vertices):
            src_size_u, src_size_v, uv_coords = self.get_uv(vertices)
            if self.autoscale:
                u_index, v_index = self.get_other_axes()
                scale_u = diameter(vertices, u_index) / src_size_u
                scale_v = diameter(vertices, v_index) / src_size_v
                scale_z = sqrt(scale_u * scale_v)
            else:
                scale_z = 1.0
            if self.flip:
                scale_z = - scale_z

            #self.info("UV: %s", uv_coords)
            surf_vertices = np.array( surf.evaluate_list(uv_coords) )
            spline_normals = np.array( operations.normal(surf, uv_coords) )[:,1,:]
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
                new_vertices = self.evaluate(surface, vertices).tolist()
                verts_out.append(new_vertices)

            self.outputs['Vertices'].sv_set(verts_out)

def register():
    if geomdl_available:
        bpy.utils.register_class(SvExBendAlongGeomdlSurface)

def unregister():
    if geomdl_available:
        bpy.utils.unregister_class(SvExBendAlongGeomdlSurface)


