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

class SvFourierCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Build Fourier Curve
    Tooltip: Create Fourier Curve from amplitude values
    """
    bl_idname = 'SvFourierCurveNode'
    bl_label = 'Build Fourier Curve'
    bl_icon = 'CURVE_NCURVE'

    omega : FloatProperty(
            name = "Omega",
            min = 0.0,
            default = pi,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Amplitudes")
        self.inputs.new('SvStringsSocket', "Omega").prop_name = 'omega'
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        amplitudes_s = self.inputs['Amplitudes'].sv_get()
        omega_s = self.inputs['Omega'].sv_get()
        input_level = get_data_nesting_level(amplitudes_s)
        amplitudes_s = ensure_nesting_level(amplitudes_s, 4)
        omega_s = ensure_nesting_level(omega_s, 2)

        nested_output = input_level > 3

        curves_out = []

        for params in zip_long_repeat(amplitudes_s, omega_s):
            new_curves = []
            for amplitudes, omega in zip_long_repeat(*params):
                if len(amplitudes) < 2:
                    raise Exception("At least 2 amplitude vectors are required")
                start = np.array(amplitudes[0])
                amplitudes = np.array(amplitudes[1:])
                curve = SvFourierCurve(omega, start, amplitudes)
                new_curves.append(curve)

            if nested_output:
                curves_out.append(new_curves)
            else:
                curves_out.extend(new_curves)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvFourierCurveNode)

def unregister():
    bpy.utils.unregister_class(SvFourierCurveNode)

