
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface
from sverchok.utils.geom import PlaneEquation

from sverchok_extra.dependencies import skimage
from sverchok_extra.utils.marching_squares import make_contours

if skimage is not None:
    from skimage import measure

    class SvExCrossSurfacePlaneNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Intersect Surface with Plane
        Tooltip: Intersect Surface with Plane
        """
        bl_idname = 'SvExCrossSurfacePlaneNode'
        bl_label = 'Intersect Surface with Plane'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EX_MSQUARES'

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

        def fill_data(self, surface, point, normal, us, vs):
            plane = PlaneEquation.from_normal_and_point(normal, point)
            d = plane.d
            surface_points = surface.evaluate_array(us, vs)
            normal = np.array(normal)
            p2 = np.apply_along_axis(lambda p : normal.dot(p), 1, surface_points)
            return p2 + d

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

                    u_min, u_max = surface.get_u_min(), surface.get_u_max()
                    v_min, v_max = surface.get_v_min(), surface.get_v_max()
                    u_range = np.linspace(u_min, u_max, num=samples_u)
                    v_range = np.linspace(v_min, v_max, num=samples_v)
                    us, vs = np.meshgrid(u_range, v_range, indexing='ij')
                    us, vs = us.flatten(), vs.flatten()

                    data = self.fill_data(surface, point, normal, us, vs)
                    data = data.reshape((samples_u, samples_v))

                    contours = measure.find_contours(data, level=0.0)

                    u_size = (u_max - u_min) / samples_u
                    v_size = (v_max - v_min) / samples_v

                    uv_new, _, _ = make_contours(samples_u, samples_v,
                                    u_min, u_size, v_min, v_size,
                                    0,
                                    contours,
                                    make_faces = False,
                                    connect_bounds = False)
                    if need_points:
                        for uv_i in uv_new:
                            us_i = [p[0] for p in uv_i]
                            vs_i = [p[1] for p in uv_i]
                            ps = surface.evaluate_array(np.array(us_i), np.array(vs_i)).tolist()
                            points_new.append(ps)

                uv_out.extend(uv_new)
                points_out.extend(points_new)

            self.outputs['Points'].sv_set(points_out)
            self.outputs['UVPoints'].sv_set(uv_out)

def register():
    if skimage is not None:
        bpy.utils.register_class(SvExCrossSurfacePlaneNode)

def unregister():
    if skimage is not None:
        bpy.utils.unregister_class(SvExCrossSurfacePlaneNode)

