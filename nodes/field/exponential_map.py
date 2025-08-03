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
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.geodesic import exponential_map, curve_exponential_map, BY_PARAMETER, BY_LENGTH

class SvExExponentialMapNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Geodesic Exponential Map
    Tooltip: Locally proportional mapping for a surface
    """
    bl_idname = 'SvExExponentialMapNode'
    bl_label = 'Proportional Mapping to Surface'
    bl_icon = 'CURVE_NCURVE'
    sv_dependencies = {'scipy'}

    map_modes = [
            ('POLAR', "Polar", "Polar mapping: circle around center", 1),
            ('CURVE', "Curve", "Curve mapping: rectangle around curve", 2)
        ]

    u_modes = [
            (BY_PARAMETER, "By Curve Parameter", "By Curve Parameter", 1),
            (BY_LENGTH, "By Curve Length", "By Curve Length", 2)
        ]

    def update_sockets(self, context):
        self.inputs['CenterUV'].hide_safe = self.map_mode != 'POLAR'
        self.inputs['UVCurve'].hide_safe = self.map_mode != 'CURVE'
        self.inputs['Radius'].label = "Radius" if self.map_mode == 'POLAR' else "V Radius"
        self.inputs['RSteps'].label = "R Steps" if self.map_mode == 'POLAR' else "V Steps"
        self.inputs['AngleSteps'].hide_safe = self.map_mode != 'POLAR'
        self.inputs['USteps'].hide_safe = self.map_mode != 'CURVE'
        self.inputs['Resolution'].hide_safe = self.map_mode != 'CURVE' or self.u_mode != BY_LENGTH
        updateNode(self, context)

    map_mode : EnumProperty(
            name = "Mode",
            items = map_modes,
            default = 'POLAR',
            update = update_sockets)

    u_mode : EnumProperty(
            name = "U Mode",
            items = u_modes,
            default = BY_PARAMETER,
            update = update_sockets)

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

    u_steps : IntProperty(
            name = "U Steps",
            default = 50,
            min = 2,
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

    len_resolution : IntProperty(
            name = "Length Resolution",
            default = 50,
            min = 1,
            update = updateNode)

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'closed_u', toggle=True)
        row.prop(self, 'closed_v', toggle=True)
        layout.prop(self, 'map_mode')
        if self.map_mode == 'CURVE':
            layout.prop(self, 'u_mode')
        layout.prop(self, 'join')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvCurveSocket', "UVCurve")

        p = self.inputs.new('SvVerticesSocket', "CenterUV")
        p.use_prop = True
        p.default_property = (0.5, 0.5, 0.0)

        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "RSteps").prop_name = 'r_steps'
        self.inputs.new('SvStringsSocket', "AngleSteps").prop_name = 'angle_steps'
        self.inputs.new('SvStringsSocket', "USteps").prop_name = 'u_steps'
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'len_resolution'

        self.outputs.new('SvVectorFieldSocket', "Field")
        self.outputs.new('SvVectorFieldSocket', "UVField")
        self.outputs.new('SvVerticesSocket', "Points")
        self.outputs.new('SvVerticesSocket', "UVPoints")
        self.outputs.new('SvVerticesSocket', "OrigPoints")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        if self.map_mode == 'POLAR':
            curve_s = [[None]]
        else:
            curve_s = self.inputs['UVCurve'].sv_get()
            curve_s = ensure_nesting_level(curve_s, 2, data_types=(SvCurve,))
        if self.map_mode == 'POLAR':
            center_s = self.inputs['CenterUV'].sv_get()
            center_s = ensure_nesting_level(center_s, 3)
        else:
            center_s = [[None]]
        radius_s = self.inputs['Radius'].sv_get()
        radius_s = ensure_nesting_level(radius_s, 2)
        r_steps_s = self.inputs['RSteps'].sv_get()
        r_steps_s = ensure_nesting_level(r_steps_s, 2)
        if self.map_mode == 'POLAR':
            angle_steps_s = self.inputs['AngleSteps'].sv_get()
            angle_steps_s = ensure_nesting_level(angle_steps_s, 2)
            u_steps_s = [[None]]
        else:
            angle_steps_s = [[None]]
            u_steps_s = self.inputs['USteps'].sv_get()
            u_steps_s = ensure_nesting_level(u_steps_s, 2)
        if self.map_mode == 'POLAR' or self.u_mode == BY_PARAMETER:
            resolution_s = [[None]]
        else:
            resolution_s = self.inputs['Resolution'].sv_get()
            resolution_s = ensure_nesting_level(resolution_s, 2)


        uv_field_out = []
        field_out = []
        points_out = []
        uv_points_out = []
        orig_points_out = []
        for params in zip_long_repeat(surface_s,
                                      center_s, curve_s,
                                      radius_s, r_steps_s, angle_steps_s,
                                      u_steps_s, resolution_s):
            new_uv_fields = []
            new_fields = []
            new_points = []
            new_uv_points = []
            new_orig_points = []
            for surface, center, curve, radius, r_steps, angle_steps, u_steps, resolution in zip_long_repeat(*params):
                if self.map_mode == 'POLAR':
                    exp_map = exponential_map(surface, center, radius,
                                              radius_steps = r_steps,
                                              angle_steps = angle_steps,
                                              closed_u = self.closed_u,
                                              closed_v = self.closed_v)
                else:
                    exp_map = curve_exponential_map(surface, curve,
                                                    v_radius = radius,
                                                    u_steps = u_steps,
                                                    v_steps = r_steps,
                                                    u_mode = self.u_mode,
                                                    length_resolution = resolution,
                                                    closed_u = self.closed_u,
                                                    closed_v = self.closed_v)
                uv_field = exp_map.get_uv_field(function='thin_plate')
                field = exp_map.get_field(function='thin_plate')
                new_uv_fields.append(uv_field)
                new_fields.append(field)
                new_points.append(exp_map.surface_points.tolist())
                new_uv_points.append(exp_map.uv_points.tolist())
                new_orig_points.append(exp_map.orig_points.tolist())
            if self.join:
                uv_field_out.extend(new_uv_fields)
                field_out.extend(new_fields)
                points_out.extend(new_points)
                uv_points_out.extend(new_uv_points)
                orig_points_out.extend(new_orig_points)
            else:
                uv_field_out.append(new_uv_fields)
                field_out.append(new_fields)
                points_out.append(new_points)
                uv_points_out.append(new_uv_points)
                orig_points_out.append(new_orig_points)

        self.outputs['Field'].sv_set(field_out)
        self.outputs['UVField'].sv_set(uv_field_out)
        if 'Points' in self.outputs:
            self.outputs['Points'].sv_set(points_out)
        if 'UVPoints' in self.outputs:
            self.outputs['UVPoints'].sv_set(uv_points_out)
        if 'OrigPoints' in self.outputs:
            self.outputs['OrigPoints'].sv_set(orig_points_out)

def register():
    bpy.utils.register_class(SvExExponentialMapNode)

def unregister():
    bpy.utils.unregister_class(SvExExponentialMapNode)

