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
from sverchok.utils.curve.nurbs_solver import SvNurbsCurvePoints

class SvNurbsCurvePointsGoalNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS Curve Point Goal
    Tooltip: NURBS Curve Goal - Points
    """
    bl_idname = 'SvNurbsCurvePointsGoalNode'
    bl_label = 'Curve Goal: Points'
    bl_icon = 'CURVE_NCURVE'

    t_value : FloatProperty(
            name = "T",
            default = 0.5,
            update = updateNode)

    weight : FloatProperty(
            name = "Weight",
            default = 1.0,
            update = updateNode)

    relative : BoolProperty(
            name = "Relative",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'relative')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
        p = self.inputs.new('SvVerticesSocket', "Point")
        p.use_prop = True
        p.default_property = (1.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Weight").prop_name = 'weight'
        self.outputs.new('SvStringsSocket', "Goal")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        ts_s = self.inputs['T'].sv_get()
        points_s = self.inputs['Point'].sv_get()
        weights_s = self.inputs['Weight'].sv_get()

        ts_s = ensure_nesting_level(ts_s, 3)
        points_s = ensure_nesting_level(points_s, 4)
        weights_s = ensure_nesting_level(weights_s, 3)

        goals_out = []
        for params in zip_long_repeat(ts_s, points_s, weights_s):
            new_goals = []
            for ts, points, weights in zip_long_repeat(*params):
                goal = SvNurbsCurvePoints(ts, points, weights, relative=self.relative)
                new_goals.append(goal)
            goals_out.append(new_goals)

        self.outputs['Goal'].sv_set(goals_out)

def register():
    bpy.utils.register_class(SvNurbsCurvePointsGoalNode)

def unregister():
    bpy.utils.unregister_class(SvNurbsCurvePointsGoalNode)

