# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, throttle_and_update_node, get_data_nesting_level, ensure_nesting_level, repeat_last_for_length
from sverchok.utils.math import supported_metrics, xyz_metrics
from sverchok.utils.curve.fourier import SvFourierCurve

class SvInterpFourierCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Interpolate Fourier Curve
    Tooltip: Interpolate Fourier Curve
    """
    bl_idname = 'SvInterpFourierCurveNode'
    bl_label = 'Interpolate Fourier Curve'
    bl_icon = 'CURVE_NCURVE'

    omega : FloatProperty(
            name = "Omega",
            min = 0.0,
            default = pi,
            update = updateNode)

    metric: EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=supported_metrics + xyz_metrics,
        update=updateNode)

    is_cyclic : BoolProperty(
            name = "Cyclic",
            description = "Make the curve cyclic (closed)",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'metric')
        layout.prop(self, 'is_cyclic')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Omega").prop_name = 'omega'
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvVerticesSocket', "Amplitudes")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        omega_s = self.inputs['Omega'].sv_get()
        input_level = get_data_nesting_level(vertices_s)
        vertices_s = ensure_nesting_level(vertices_s, 4)
        omega_s = ensure_nesting_level(omega_s, 2)

        nested_output = input_level > 3

        curves_out = []
        points_out = []

        for params in zip_long_repeat(vertices_s, omega_s):
            new_curves = []
            new_points = []
            for vertices, omega in zip_long_repeat(*params):
                curve = SvFourierCurve.interpolate(np.array(vertices), omega, metric=self.metric, is_cyclic = self.is_cyclic)
                amplitudes = [tuple(curve.start)] + curve.coeffs.tolist()

                new_curves.append(curve)
                new_points.append(amplitudes)

            if nested_output:
                curves_out.append(new_curves)
                points_out.append(new_points)
            else:
                curves_out.extend(new_curves)
                points_out.extend(new_points)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['Amplitudes'].sv_set(points_out)

def register():
    bpy.utils.register_class(SvInterpFourierCurveNode)

def unregister():
    bpy.utils.unregister_class(SvInterpFourierCurveNode)

