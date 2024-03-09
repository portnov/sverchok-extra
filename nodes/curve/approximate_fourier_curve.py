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
from sverchok.utils.math import supported_metrics, xyz_metrics
from sverchok.utils.curve.fourier import SvFourierCurve
from sverchok.dependencies import scipy

class SvApproxFourierCurveNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Approximate Fourier Curve
    Tooltip: Approximate Fourier Curve
    """
    bl_idname = 'SvApproxFourierCurveNode'
    bl_label = 'Approximate Fourier Curve'
    bl_icon = 'CURVE_NCURVE'
    sv_dependencies = {'scipy'}

    degree : IntProperty(
            name = "Degree",
            min = 1, max = 6,
            default = 3,
            update = updateNode)

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=supported_metrics + xyz_metrics,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvStringsSocket', "Omega")
        self.outputs.new('SvVerticesSocket', "Amplitudes")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        degree_s = self.inputs['Degree'].sv_get()
        input_level = get_data_nesting_level(vertices_s)
        vertices_s = ensure_nesting_level(vertices_s, 4)
        degree_s = ensure_nesting_level(degree_s, 2)

        nested_output = input_level > 3

        curves_out = []
        points_out = []
        omega_out = []

        for params in zip_long_repeat(vertices_s, degree_s):
            new_curves = []
            new_points = []
            new_omega = []
            for vertices, degree in zip_long_repeat(*params):
                curve = SvFourierCurve.approximate(np.array(vertices), degree, metric=self.metric)
                amplitudes = [tuple(curve.start)] + curve.coeffs.tolist()
                omega = curve.omega

                new_curves.append(curve)
                new_points.append(amplitudes)
                new_omega.append(omega)

            if nested_output:
                curves_out.append(new_curves)
                points_out.append(new_points)
            else:
                curves_out.extend(new_curves)
                points_out.extend(new_points)

            omega_out.append(new_omega)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['Omega'].sv_set(omega_out)
        self.outputs['Amplitudes'].sv_set(points_out)

def register():
    bpy.utils.register_class(SvApproxFourierCurveNode)

def unregister():
    bpy.utils.unregister_class(SvApproxFourierCurveNode)
