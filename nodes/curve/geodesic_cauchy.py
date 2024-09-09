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
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, repeat_last_for_length
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.curve.algorithms import SvCurveOnSurface
from sverchok.utils.math import np_multiply_matrices_vectors

from sverchok.utils.geodesic import geodesic_cauchy_problem, cubic_spline

def calc_angles(surface, uvs, directions):
    n = len(uvs)
    uvs = np.asarray(uvs)
    directions = np.asarray(directions)
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    data = surface.derivatives_data_array(uvs[:,0], uvs[:,1])
    normals = data.unit_normals()
    du1, dv1 = data.unit_tangents()
    #print(np_dot(directions, dv1))
    dy = np.cross(du1, normals)
    matrices = np.zeros((n,3,3))
    matrices[:,:,0] = du1
    matrices[:,:,1] = dy
    matrices[:,:,2] = normals
    inv = np.linalg.inv(matrices)
    res = np_multiply_matrices_vectors(inv, directions)
    return np.arctan2(res[:,1], res[:,0])

class SvExGeodesicCauchyNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Geodesic Curve by point and direction
    Tooltip: Calculate geodesic curves on a surface
    """
    bl_idname = 'SvExGeodesicCauchyNode'
    bl_label = 'Geodesic Curve by Point and Direction'
    bl_icon = 'CURVE_NCURVE'

    angle : FloatProperty(
            name = "Angle",
            default = 0.0,
            update = updateNode)

    distance : FloatProperty(
            name = "Distance",
            default = 1.0,
            min = 0.0,
            update = updateNode)

    steps : IntProperty(
            name = "N Steps",
            default = 50,
            min = 1,
            update = updateNode)

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
        description = "If checked, output single flat list of curves for all sets of inputs",
        default = True,
        update = updateNode)

    def update_sockets(self, context):
        self.inputs['Direction'].hide_safe = self.angle_mode == 'ANGLE'
        self.inputs['Angle'].hide_safe = self.angle_mode == 'DIRECTION'

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'closed_u', toggle=True)
        row.prop(self, 'closed_v', toggle=True)
        layout.prop(self, 'angle_mode')
        layout.prop(self, 'join')

    modes = [
            ('ANGLE', "By Angle", "Angle", 0),
            ('DIRECTION', "By 3D Direction", "Direction", 1)
        ]

    angle_mode : EnumProperty(
            name = "Specify direction",
            items = modes,
            default = 'ANGLE',
            update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")

        p = self.inputs.new('SvVerticesSocket', "StartUV")
        p.use_prop = True
        p.default_property = (0.5, 0.5, 0.0)

        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'

        p = self.inputs.new('SvVerticesSocket', "Direction")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 1.0)

        self.inputs.new('SvStringsSocket', "Distance").prop_name = 'distance'
        self.inputs.new('SvStringsSocket', "NSteps").prop_name = 'steps'

        self.outputs.new('SvVerticesSocket', "Points")
        self.outputs.new('SvVerticesSocket', "UVPoints")
        self.outputs.new('SvVerticesSocket', "OrigPoints")
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvCurveSocket', "UVCurve")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface_s = self.inputs['Surface'].sv_get()
        surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
        start_s = self.inputs['StartUV'].sv_get()
        start_s = ensure_nesting_level(start_s, 4)
        distance_s = self.inputs['Distance'].sv_get()
        distance_s = ensure_nesting_level(distance_s, 2)
        steps_s = self.inputs['NSteps'].sv_get()
        steps_s = ensure_nesting_level(steps_s, 2)

        if self.angle_mode == 'ANGLE':
            angle_s = self.inputs['Angle'].sv_get()
            angle_s =ensure_nesting_level(angle_s, 3)
            direction_s = [[None]]
        else:
            angle_s = [[None]]
            direction_s = self.inputs['Direction'].sv_get()
            direction_s = ensure_nesting_level(direction_s, 4)

        points_out = []
        uv_points_out = []
        orig_points_out = []
        uv_curves_out = []
        curves_out = []
        for params in zip_long_repeat(surface_s, start_s, angle_s, direction_s, distance_s, steps_s):
            new_points = []
            new_uv_points = []
            new_orig_points = []
            new_uv_curves = []
            new_curves = []

            for surface, starts, angles, directions, distance, steps in zip_long_repeat(*params):
                n = len(starts)
                if self.angle_mode == 'DIRECTION':
                    m = len(directions)
                    k = max(n, m)
                    directions = repeat_last_for_length(directions, k)
                    angles = calc_angles(surface, starts, directions)
                    starts = repeat_last_for_length(starts, k)
                else:
                    m = len(angles)
                    k = max(n, m)
                    angles = repeat_last_for_length(angles, k)
                    angles = np.array(angles)
                    starts = repeat_last_for_length(starts, k)
                starts = np.array(starts)
                solution = geodesic_cauchy_problem(surface, starts,
                                                   angles, distance,
                                                   steps,
                                                   closed_u = self.closed_u,
                                                   closed_v = self.closed_v)
                uv_curve = [cubic_spline(surface, uv_points) for uv_points in solution.uv_points]
                curve = [SvCurveOnSurface(uv, surface, axis=2) for uv in uv_curve]

                new_orig_points.append(solution.orig_points)
                new_uv_points.append(solution.uv_points)
                new_points.append(solution.surface_points)
                new_uv_curves.append(uv_curve)
                new_curves.append(curve)

            if self.join:
                uv_curves_out.extend(new_uv_curves)
                uv_points_out.extend(new_uv_points)
                curves_out.extend(new_curves)
                points_out.extend(new_points)
                orig_points_out.extend(new_orig_points)
            else:
                uv_curves_out.append(new_uv_curves)
                uv_points_out.append(new_uv_points)
                curves_out.append(new_curves)
                points_out.append(new_points)
                orig_points_out.append(new_orig_points)

        self.outputs['UVCurve'].sv_set(uv_curves_out)
        self.outputs['UVPoints'].sv_set(uv_points_out)
        self.outputs['OrigPoints'].sv_set(orig_points_out)
        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['Points'].sv_set(points_out)

def register():
    bpy.utils.register_class(SvExGeodesicCauchyNode)

def unregister():
    bpy.utils.unregister_class(SvExGeodesicCauchyNode)


