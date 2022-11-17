
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface
from sverchok.utils.geom import PlaneEquation
from sverchok.dependencies import scipy, skimage

from sverchok_extra.utils.manifolds import intersect_surface_plane_msquares, intersect_surface_plane_uv


class SvExCrossSurfacePlaneNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Intersect Surface with Plane
    Tooltip: Intersect Surface with Plane
    """
    bl_idname = 'SvExCrossSurfacePlaneNode'
    bl_label = 'Intersect Surface with Plane'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_MSQUARES'
    sv_dependencies = {'skimage', 'scipy'}

    samples_u : IntProperty(
            name = "Samples U",
            default = 50,
            min = 4,
            update = updateNode)

    samples_v : IntProperty(
            name = "Samples V",
            default = 50,
            min = 4,
            update = updateNode)

    init_samples : IntProperty(
        name = "Init Resolution",
        default = 10,
        min = 3,
        update = updateNode)

    def get_modes(self, context):
        modes = []
        if skimage is not None:
            modes.append(('skimage', "Marching Squares", "Use marching squares algorithm", 0))
        if scipy is not None:
            modes.append(('scipy', "OP + Tangent (Unsorted!)", "Use orthogonal projections + tangent method", 1))
        return modes

    def update_sockets(self, context):
        self.outputs['UVPoints'].hide_safe = self.algorithm != 'skimage'
        updateNode(self, context)

    algorithm : EnumProperty(
            name = "Algorithm",
            items = get_modes,
            update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        d = self.inputs.new('SvVerticesSocket', "Point")
        d.use_prop = True
        d.prop = (0.0, 0.0, 0.0)
        d = self.inputs.new('SvVerticesSocket', "Normal")
        d.use_prop = True
        d.prop = (0.0, 0.0, 1.0)
        self.inputs.new('SvStringsSocket', "SamplesU").prop_name = 'samples_u'
        self.inputs.new('SvStringsSocket', "SamplesV").prop_name = 'samples_v'
        self.outputs.new('SvVerticesSocket', "Points")
        self.outputs.new('SvVerticesSocket', "UVPoints")
        self.update_socket(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'algorithm', text='')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context)
        if self.algorithm == 'scipy':
            layout.prop(self, 'init_samples')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        point_s = self.inputs['Point'].sv_get()
        normal_s = self.inputs['Normal'].sv_get()
        samples_u_s = self.inputs['SamplesU'].sv_get()
        samples_v_s = self.inputs['SamplesV'].sv_get()

        surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))

        need_points = self.outputs['Points'].is_linked

        uv_out = []
        points_out = []
        for surfaces, points, normals, samples_u_i, samples_v_i in zip_long_repeat(surfaces_s, point_s, normal_s, samples_u_s, samples_v_s):
            uv_new = []
            points_new = []
            for surface, point, normal, samples_u, samples_v in zip_long_repeat(surfaces, points, normals, samples_u_i, samples_v_i):
                plane = PlaneEquation.from_normal_and_point(normal, point)
                if self.algorithm == 'skimage':
                    uv_new, points_new = intersect_surface_plane_msquares(surface, plane,
                                            need_points = need_points,
                                            samples_u = samples_u, samples_v = samples_v)
                else:
                    points_new = intersect_surface_plane_uv(surface, plane,
                                    samples_u = samples_u, samples_v = samples_v,
                                    init_samples = self.init_samples, ortho_samples = self.init_samples)
                    points_new = [points_new]

            uv_out.extend(uv_new)
            points_out.extend(points_new)

        self.outputs['Points'].sv_set(points_out)
        self.outputs['UVPoints'].sv_set(uv_out)


def register():
    bpy.utils.register_class(SvExCrossSurfacePlaneNode)


def unregister():
    bpy.utils.unregister_class(SvExCrossSurfacePlaneNode)
