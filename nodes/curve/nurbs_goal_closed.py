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
from sverchok.utils.curve.nurbs_solver import SvNurbsCurveSelfIntersections, SvNurbsCurveCotangents

class SvNurbsCurveClosedGoalNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS Curve Closed Goal
    Tooltip: NURBS Curve Goal - Closed
    """
    bl_idname = 'SvNurbsCurveClosedGoalNode'
    bl_label = 'Curve Goal: Closed'
    bl_icon = 'CURVE_NCURVE'

    weight : FloatProperty(
            name = "Weight",
            default = 1.0,
            update = updateNode)

    tangents : BoolProperty(
            name = "Coinciding Tangents",
            default = True,
            update = updateNode)

    relative : BoolProperty(
            name = "Relative",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'tangents')
        layout.prop(self, 'relative')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Weight").prop_name = 'weight'
        self.outputs.new('SvStringsSocket', "Goal")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        weights_s = self.inputs['Weight'].sv_get()
        weights_s = ensure_nesting_level(weights_s, 2)

        goals_out = []
        for params in weights_s:
            new_goals = []
            for weight in params:
                closed = SvNurbsCurveSelfIntersections.single(0.0, 1.0, weight, relative_u=True, relative=self.relative)
                if self.tangents:
                    tangents = SvNurbsCurveCotangents.single(0.0, 1.0, weight, relative_u=True, relative=self.relative)
                    goals = [closed, tangents]
                else:
                    goals = [closed]
                new_goals.append(goals)
            goals_out.append(new_goals)

        self.outputs['Goal'].sv_set(goals_out)

def register():
    bpy.utils.register_class(SvNurbsCurveClosedGoalNode)

def unregister():
    bpy.utils.unregister_class(SvNurbsCurveClosedGoalNode)

