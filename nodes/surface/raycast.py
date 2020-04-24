import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface

from sverchok_extra.dependencies import scipy

if scipy is not None:
    from scipy.optimize import root

    def make_faces(samples):
        faces = []
        for row in range(samples - 1):
            for col in range(samples - 1):
                i = row * samples + col
                face = (i, i+samples, i+samples+1, i+1)
                faces.append(face)
        return faces

    def init_guess(surface, src_points, directions, samples=50):
        u_min = surface.get_u_min()
        u_max = surface.get_u_max()
        v_min = surface.get_v_min()
        v_max = surface.get_v_max()
        us = np.linspace(u_min, u_max, num=samples)
        vs = np.linspace(v_min, v_max, num=samples)
        us, vs = np.meshgrid(us, vs)
        us = us.flatten()
        vs = vs.flatten()

        points = surface.evaluate_array(us, vs).tolist()
        faces = make_faces(samples)

        bvh = BVHTree.FromPolygons(points, faces)

        us_out = []
        vs_out = []
        t_out = []
        nearest_out = []
        h2 = (u_max - u_min) / (2 * samples)
        for src_point, direction in zip(src_points, directions):
            nearest, normal, index, distance = bvh.ray_cast(src_point, direction)
            us_out.append(us[index] + h2)
            vs_out.append(vs[index] + h2)
            t_out.append(distance)
            nearest_out.append(tuple(nearest))

        return us_out, vs_out, t_out, nearest_out

    def goal(surface, src_point, direction):
        def function(p):
            on_surface = surface.evaluate(p[0], p[1])
            on_line = src_point + direction * p[2]
            return (on_surface - on_line).flatten()
        return function

    class SvExRaycastSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Raycast on Surface
        Tooltip: Raycast on Surface
        """
        bl_idname = 'SvExRaycastSurfaceNode'
        bl_label = 'Raycast on Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EVAL_SURFACE'

        samples : IntProperty(
            name = "Init Resolution",
            default = 10,
            min = 3,
            update = updateNode)
        
        precise : BoolProperty(
            name = "Precise",
            default = True,
            update = updateNode)

        @throttled
        def update_sockets(self, context):
            self.inputs['Source'].hide_safe = self.project_mode != 'CONIC'
            self.inputs['Direction'].hide_safe = self.project_mode != 'PARALLEL'

        modes = [
            ('PARALLEL', "Along Direction", "Project points along specified direction", 0),
            ('CONIC', "From Source", "Project points along the direction from the source point", 1)
        ]

        project_mode : EnumProperty(
            name = "Project",
            items = modes,
            default = 'PARALLEL',
            update = update_sockets)

        methods = [
            ('hybr', "Hybrd & Hybrj", "Use MINPACK’s hybrd and hybrj routines (modified Powell method)", 0),
            ('lm', "Levenberg-Marquardt", "Levenberg-Marquardt algorithm", 1),
            ('krylov', "Krylov", "Krylov algorithm", 2),
            ('broyden1', "Broyden 1", "Broyden1 algorithm", 3),
            ('broyden2', "Broyden 2", "Broyden2 algorithm", 4)
        ]

        method : EnumProperty(
            name = "Method",
            items = methods,
            default = 'hybr',
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.label(text="Project:")
            layout.prop(self, 'project_mode', text='')
            layout.prop(self, 'samples')
            layout.prop(self, 'precise', toggle=True)

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            if self.precise:
                layout.prop(self, 'method')

        def sv_init(self, context):
            self.inputs.new('SvSurfaceSocket', "Surface")
            p = self.inputs.new('SvVerticesSocket', "Source")
            p.use_prop = True
            p.prop = (0.0, 0.0, 1.0)
            p = self.inputs.new('SvVerticesSocket', "Point")
            p.use_prop = True
            p.prop = (0.0, 0.0, 1.0)
            p = self.inputs.new('SvVerticesSocket', "Direction")
            p.use_prop = True
            p.prop = (0.0, 0.0, -1.0)
            self.outputs.new('SvVerticesSocket', "Point")
            self.outputs.new('SvVerticesSocket', "UVPoint")
            self.update_sockets(context)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            surfaces_s = self.inputs['Surface'].sv_get()
            surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
            src_point_s = self.inputs['Source'].sv_get()
            src_point_s = ensure_nesting_level(src_point_s, 4)
            points_s = self.inputs['Point'].sv_get()
            points_s = ensure_nesting_level(points_s, 4)
            direction_s = self.inputs['Direction'].sv_get()
            direction_s = ensure_nesting_level(direction_s, 4)

            points_out = []
            points_uv_out = []
            for surfaces, src_points_i, points_i, directions_i in zip_long_repeat(surfaces_s, src_point_s, points_s, direction_s):
                for surface, src_points, points, directions in zip_long_repeat(surfaces, src_points_i, points_i, directions_i):
                    u_min = surface.get_u_min()
                    u_max = surface.get_u_max()
                    v_min = surface.get_v_min()
                    v_max = surface.get_v_max()

                    new_uv = []
                    new_u = []
                    new_v = []
                    new_points = []

                    if self.project_mode == 'PARALLEL':
                        directions = repeat_last_for_length(directions, len(points))
                    else: # CONIC
                        src_points = repeat_last_for_length(src_points, len(points))
                        directions = (np.array(points) - np.array(src_points)).tolist()

                    init_us, init_vs, init_ts, init_points = init_guess(surface, points, directions, samples=self.samples)
                    for point, direction, init_u, init_v, init_t, init_point in zip(points, directions, init_us, init_vs, init_ts, init_points):
                        if self.precise:
                            direction = np.array(direction)
                            direction = direction / np.linalg.norm(direction)
                            result = root(goal(surface, np.array(point), direction),
                                        x0 = np.array([init_u, init_v, init_t]),
                                        method = self.method)
                            if not result.success:
                                raise Exception("Can't find the projection for {}: {}".format(point, result.message))
                            u0, v0, t0 = result.x
                        else:
                            u0, v0 = init_u, init_v
                            new_points.append(init_point)

                        new_uv.append((u0, v0, 0))
                        new_u.append(u0)
                        new_v.append(v0)

                    if self.precise and self.outputs['Point'].is_linked:
                        new_points = surface.evaluate_array(np.array(new_u), np.array(new_v)).tolist()

                    points_out.append(new_points)
                    points_uv_out.append(new_uv)

            self.outputs['Point'].sv_set(points_out)
            self.outputs['UVPoint'].sv_set(points_uv_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExRaycastSurfaceNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExRaycastSurfaceNode)

