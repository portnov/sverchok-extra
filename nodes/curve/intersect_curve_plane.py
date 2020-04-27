
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.geom import PlaneEquation

from sverchok_extra.utils.geom import intersect_curve_plane
from sverchok_extra.dependencies import scipy

if scipy is not None:

    class SvExCrossCurvePlaneNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Intersect Curve with Plane
        Tooltip: Intersect Curve with Plane
        """
        bl_idname = 'SvExCrossCurvePlaneNode'
        bl_label = 'Intersect Curve with Plane'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EX_MSQUARES'

        samples : IntProperty(
            name = "Init Resolution",
            default = 10,
            min = 3,
            update = updateNode)

#         join : BoolProperty(
#             name = "Join",
#             default = True,
#             update = updateNode)

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context)
            layout.prop(self, 'samples')
            
        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            d = self.inputs.new('SvVerticesSocket', "Point")
            d.use_prop = True
            d.prop = (0.0, 0.0, 0.0)
            d = self.inputs.new('SvVerticesSocket', "Normal")
            d.use_prop = True
            d.prop = (0.0, 0.0, 1.0)
            self.outputs.new('SvVerticesSocket', "Point")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curves_s = self.inputs['Curve'].sv_get()
            point_s = self.inputs['Point'].sv_get()
            normal_s = self.inputs['Normal'].sv_get()
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

            points_out = []

            for curves, points, normals in zip_long_repeat(curves_s, point_s, normal_s):
                new_points = []
                for curve, point, normal in zip_long_repeat(curves, points, normals):
                    plane = PlaneEquation.from_normal_and_point(normal, point)
                    ps = intersect_curve_plane(curve, plane, init_samples = self.samples, ortho_samples = self.samples)
                    new_points.extend(ps)

                points_out.append(new_points)

            self.outputs['Point'].sv_set(points_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExCrossCurvePlaneNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExCrossCurvePlaneNode)

