
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.geom import LinearSpline, CubicSpline

from sverchok_extra.data.surface import SvExInterpolatingSurface
from sverchok_extra.data.curve import SvExGeomdlCurve, SvExSplineCurve
from sverchok_extra.dependencies import geomdl

if geomdl is not None:
    from geomdl import fitting

    class SvExInterpolatingSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Interpolating surface from curves
        Tooltip: Generate interpolating surface across several curves
        """
        bl_idname = 'SvExInterpolatingSurfaceNode'
        bl_label = 'Surface from Curves'
        bl_icon = 'OUTLINER_OB_EMPTY'

        interp_modes = [
            ('LIN', "Linear", "Linear interpolation", 0),
            ('CUBIC', "Cubic", "Cubic interpolation", 1),
            ('BSPLINE', "B-Spline", "B-Spline interpolation", 2)
        ]

        @throttled
        def update_sockets(self, context):
            self.inputs['Degree'].hide_safe = self.interp_mode != 'BSPLINE'

        interp_mode : EnumProperty(
            name = "Interpolation mode",
            items = interp_modes,
            default = 'CUBIC',
            update = update_sockets)

        is_cyclic : BoolProperty(
            name = "Cyclic",
            default = False,
            update = updateNode)

        centripetal : BoolProperty(
                name = "Centripetal",
                default = False,
                update = updateNode)

        degree : IntProperty(
                name = "Degree",
                min = 2, max = 6,
                default = 3,
                update = updateNode)

        def get_u_spline_constructor(self, degree):
            if self.interp_mode == 'LIN':
                def make(vertices):
                    spline = LinearSpline(vertices, metric='DISTANCE', is_cyclic=self.is_cyclic)
                    return SvExSplineCurve(spline)
                return make
            elif self.interp_mode == 'CUBIC':
                def make(vertices):
                    spline = CubicSpline(vertices, metric='DISTANCE', is_cyclic=self.is_cyclic)
                    return SvExSplineCurve(spline)
                return make
            elif self.interp_mode == 'BSPLINE':
                def make(vertices):
                    curve = fitting.interpolate_curve(vertices, degree, centripetal=self.centripetal)
                    return SvExGeomdlCurve(curve)
                return make
            else:
                raise Exception("Unsupported spline type!")

        def draw_buttons(self, context, layout):
            layout.prop(self, 'interp_mode', expand=True)
            if self.interp_mode == 'BSPLINE':
                layout.prop(self, 'centripetal', toggle=True)
            if self.interp_mode in {'LIN', 'CUBIC'}:
                layout.prop(self, 'is_cyclic', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvExCurveSocket', "Curves").display_shape = 'DIAMOND'
            self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
            self.outputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'
            self.update_sockets(context)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curves_s = self.inputs['Curves'].sv_get()
            degree_s = self.inputs['Degree'].sv_get()

            if not isinstance(curves_s[0], (list, tuple)):
                curves_s = [curves_s]

            surfaces_out = []
            for curves, degree in zip_long_repeat(curves_s, degree_s):
                if isinstance(degree, (list, tuple)):
                    degree = degree[0]
                u_spline_constructor = self.get_u_spline_constructor(degree)
                v_bounds = curves[0].get_u_bounds()
                u_bounds = (0.0, 1.0)
                surface = SvExInterpolatingSurface(u_bounds, v_bounds, u_spline_constructor, curves)
                surfaces_out.append(surface)

            self.outputs['Surface'].sv_set(surfaces_out)

def register():
    if geomdl is not None:
        bpy.utils.register_class(SvExInterpolatingSurfaceNode)

def unregister():
    if geomdl is not None:
        bpy.utils.unregister_class(SvExInterpolatingSurfaceNode)

