
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.logging import info, exception
from sverchok.utils.math import inverse, inverse_square, inverse_cubic

from sverchok_extra.data import SvExScalarFieldPointDistance

def inverse_exp(c, x):
    return np.exp(-c*x)

def gauss(c, x):
    return np.exp(-c*x*x/2.0)

class SvExScalarFieldPointNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Point
    Tooltip: Generate scalar field by distance from a point
    """
    bl_idname = 'SvExScalarFieldPointNode'
    bl_label = 'Distance from a point'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    falloff_types = [
            ('NONE', "None - R", "Output distance", 0),
            ("inverse", "Inverse - 1/R", "", 1),
            ("inverse_square", "Inverse square - 1/R^2", "Similar to gravitation or electromagnetizm", 2),
            ("inverse_cubic", "Inverse cubic - 1/R^3", "", 3),
            ("inverse_exp", "Inverse exponent - Exp(-R)", "", 4),
            ("gauss", "Gauss - Exp(-R^2/2)", "", 5)
        ]

    @throttled
    def update_type(self, context):
        self.inputs['Amplitude'].hide_safe = (self.falloff_type != 'NONE')
        self.inputs['Coefficient'].hide_safe = (self.falloff_type not in ['NONE', 'inverse_exp', 'gauss'])

    falloff_type: EnumProperty(
        name="Falloff type", items=falloff_types, default='NONE', update=update_type)

    amplitude: FloatProperty(
        name="Amplitude", default=0.5, min=0.0, update=updateNode)

    coefficient: FloatProperty(
        name="Coefficient", default=0.5, update=updateNode)

    clamp: BoolProperty(
        name="Clamp", description="Restrict coefficient with R", default=False, update=updateNode)

    def sv_init(self, context):
        d = self.inputs.new('SvVerticesSocket', "Center")
        d.use_prop = True
        d.prop = (0.0, 0.0, 0.0)

        self.inputs.new('SvStringsSocket', 'Amplitude').prop_name = 'amplitude'
        self.inputs.new('SvStringsSocket', 'Coefficient').prop_name = 'coefficient'

        self.outputs.new('SvExScalarFieldSocket', "Field").display_shape = 'CIRCLE_DOT'
        self.update_type(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'falloff_type')
        layout.prop(self, 'clamp')

    def falloff(self, amplitude, coefficient):
        falloff_func = globals()[self.falloff_type]

        def function(rho_array):
            zero_idxs = (rho_array == 0)
            nonzero = (rho_array != 0)
            result = np.empty_like(rho_array)
            result[zero_idxs] = amplitude
            result[nonzero] = amplitude * falloff_func(coefficient, rho_array[nonzero])
            negative = result <= 0
            result[negative] = 0.0

            if self.clamp:
                high = result >= rho_array
                result[high] = rho_array[high]
            return result
        return function

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get()
        amplitudes_s = self.inputs['Amplitude'].sv_get(default=[0.5])
        coefficients_s = self.inputs['Coefficient'].sv_get(default=[0.5])

        fields_out = []
        for centers, amplitudes, coefficients in zip_long_repeat(center_s, amplitudes_s, coefficients_s):
            for center, amplitude, coefficient in zip_long_repeat(centers, amplitudes, coefficients):
                if self.falloff_type == 'NONE':
                    falloff = None
                else:
                    falloff = self.falloff(amplitude, coefficient)
                field = SvExScalarFieldPointDistance(np.array(center), falloff)
                fields_out.append(field)

        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvExScalarFieldPointNode)

def unregister():
    bpy.utils.unregister_class(SvExScalarFieldPointNode)


