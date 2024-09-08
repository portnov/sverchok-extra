# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level, repeat_last_for_length
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.geom import Spline, CubicSpline
from sverchok.utils.curve.splines import SvSplineCurve

from sverchok.utils.geodesic import geodesic_curve_by_two_points, cubic_spline

class SvExGeodesicCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Geodesic Curve
    Tooltip: Calculate geodesic curves on a surface
    """
    bl_idname = 'SvExGeodesicCurveNode'
    bl_label = 'Geodesic Curve'
    bl_icon = 'CURVE_NCURVE'

    n_points : IntProperty(
        name = "N Points",
        description = "Number of key points to build interpolation",
        min = 3,
        default = 10,
        update = updateNode)

    n_iterations : IntProperty(
        name = "Iterations",
        description = "Maximum number of iterations",
        min = 0,
        default = 10,
        update = updateNode)

    step : FloatProperty(
        name = "Step",
        description = "Iteration step multiplier",
        min = 1e-10,
        default = 0.01,
        precision = 8,
        update = updateNode)

    tolerance : FloatProperty(
        name = "Tolerance",
        description = "Minimum step after which to stop iterations",
        min = 1e-10,
        default = 0.001,
        precision = 8,
        update = updateNode)

    join : BoolProperty(
        name = "Join",
        description = "If checked, output single flat list of curves for all sets of inputs",
        default = True,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")

        p = self.inputs.new('SvVerticesSocket', "UVPoint1")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 0.0)
        p = self.inputs.new('SvVerticesSocket', "UVPoint2")
        p.use_prop = True
        p.default_property = (1.0, 1.0, 0.0)

        self.inputs.new('SvStringsSocket', "N Points").prop_name = 'n_points'
        self.inputs.new('SvStringsSocket', "Iterations").prop_name = 'n_iterations'
        self.inputs.new('SvStringsSocket', "Step").prop_name = 'step'
        self.inputs.new('SvStringsSocket', "Tolerance").prop_name = 'tolerance'

        self.outputs.new('SvCurveSocket', "UVCurve")
        self.outputs.new('SvVerticesSocket', "UVPoints")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'join')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        point1_s = self.inputs['UVPoint1'].sv_get()
        point2_s = self.inputs['UVPoint2'].sv_get()
        n_points_s = self.inputs['N Points'].sv_get()
        n_iterations_s = self.inputs['Iterations'].sv_get()
        step_s = self.inputs['Step'].sv_get()
        tolerance_s = self.inputs['Tolerance'].sv_get()

        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        point1_s = ensure_nesting_level(point1_s, 3)
        point2_s = ensure_nesting_level(point2_s, 3)
        n_points_s = ensure_nesting_level(n_points_s, 2)
        n_iterations_s = ensure_nesting_level(n_iterations_s, 2)
        step_s = ensure_nesting_level(step_s, 2)
        tolerance_s = ensure_nesting_level(tolerance_s, 2)

        curves_out = []
        uv_points_out = []
        for params in zip_long_repeat(surface_s, point1_s, point2_s, n_points_s, n_iterations_s, step_s, tolerance_s):
            new_curves = []
            new_uv_pts = []
            for surface, point1, point2, n_points, n_iterations, step, tolerance in zip_long_repeat(*params):
                uv_pts = geodesic_curve_by_two_points(surface, point1, point2, n_points, n_iterations, step, tolerance, logger=self.sv_logger)
                curve = cubic_spline(surface, uv_pts)
                new_curves.append(curve)
                new_uv_pts.append(uv_pts)

            if self.join:
                curves_out.extend(new_curves)
                uv_points_out.extend(new_uv_pts)
            else:
                curves_out.append(new_curves)
                uv_points_out.append(new_uv_pts)

        self.outputs['UVCurve'].sv_set(curves_out)
        self.outputs['UVPoints'].sv_set(uv_points_out)

def register():
    bpy.utils.register_class(SvExGeodesicCurveNode)

def unregister():
    bpy.utils.unregister_class(SvExGeodesicCurveNode)

