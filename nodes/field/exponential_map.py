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
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.curve.algorithms import SvCurveOnSurface
from sverchok.utils.math import np_multiply_matrices_vectors
from sverchok.utils.geodesic import exponential_map

class SvExExponentialMapNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Geodesic Exponential Map
    Tooltip: Local geodesic mapping for a surface
    """
    bl_idname = 'SvExExponentialMapNode'
    bl_label = 'Geodesic Mapping'
    bl_icon = 'CURVE_NCURVE'
    sv_dependencies = {'scipy'}

    closed_u : BoolProperty(
            name = "Closed U",
            default = False,
            update = updateNode)

    closed_v : BoolProperty(
            name = "Closed V",
            default = False,
            update = updateNode)

    join : BoolProperty(
        name = "Join",
        description = "If checked, output single flat list of fields for all sets of inputs",
        default = True,
        update = updateNode)

    radius : FloatProperty(
            name = "Radius",
            default = 1.0,
            min = 0.0,
            update = updateNode)

    r_steps : IntProperty(
            name = "R Steps",
            default = 50,
            min = 1,
            update = updateNode)

    angle_steps : IntProperty(
            name = "Angle Steps",
            default = 16,
            min = 1,
            update = updateNode)

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'closed_u', toggle=True)
        row.prop(self, 'closed_v', toggle=True)
        layout.prop(self, 'join')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")

        p = self.inputs.new('SvVerticesSocket', "CenterUV")
        p.use_prop = True
        p.default_property = (0.5, 0.5, 0.0)

        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "RSteps").prop_name = 'r_steps'
        self.inputs.new('SvStringsSocket', "AngleSteps").prop_name = 'angle_steps'

        self.outputs.new('SvVectorFieldSocket', "Field")
        self.outputs.new('SvVectorFieldSocket', "UVField")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        center_s = self.inputs['CenterUV'].sv_get()
        center_s = ensure_nesting_level(center_s, 3)
        radius_s = self.inputs['Radius'].sv_get()
        radius_s = ensure_nesting_level(radius_s, 2)
        r_steps_s = self.inputs['RSteps'].sv_get()
        r_steps_s = ensure_nesting_level(r_steps_s, 2)
        angle_steps_s = self.inputs['AngleSteps'].sv_get()
        angle_steps_s = ensure_nesting_level(angle_steps_s, 2)

        uv_field_out = []
        field_out = []
        for params in zip_long_repeat(surface_s, center_s, radius_s, r_steps_s, angle_steps_s):
            new_uv_fields = []
            new_fields = []
            for surface, center, radius, r_steps, angle_steps in zip_long_repeat(*params):
                exp_map = exponential_map(surface, center, radius,
                                          radius_steps = r_steps,
                                          angle_steps = angle_steps,
                                          closed_u = self.closed_u,
                                          closed_v = self.closed_v)
                uv_field = exp_map.get_uv_field()
                field = exp_map.get_field()
                new_uv_fields.append(uv_field)
                new_fields.append(field)
            if self.join:
                uv_field_out.extend(new_uv_fields)
                field_out.extend(new_fields)
            else:
                uv_field_out.append(new_uv_fields)
                field_out.append(new_fields)

        self.outputs['Field'].sv_set(field_out)
        self.outputs['UVField'].sv_set(uv_field_out)

def register():
    bpy.utils.register_class(SvExExponentialMapNode)

def unregister():
    bpy.utils.unregister_class(SvExExponentialMapNode)

