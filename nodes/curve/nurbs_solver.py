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
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_solver import SvNurbsCurveSolver, SvNurbsCurveGoal

class SvNurbsCurveSolverNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS Curve Solver
    Tooltip: NURBS Curve Solver
    """
    bl_idname = 'SvNurbsCurveSolverNode'
    bl_label = 'NURBS Curve Solver'
    bl_icon = 'CURVE_NCURVE'

    modes = [
            ('GUESS', "Guess", "Guess curve parameters from goals", 0),
            ('EXPLICIT', "Specify", "Specify curve parameters explicitly", 1),
            ('CURVE', "Curve", "Use curve parameters from initial curve", 2)
        ]

    def update_sockets(self, context):
        self.inputs['Degree'].hide_safe = self.mode == 'CURVE'
        self.inputs['NControlPoints'].hide_safe = self.mode != 'EXPLICIT'
        self.inputs['Knotvector'].hide_safe = self.mode != 'EXPLICIT'
        self.inputs['CurveWeights'].hide_safe = self.mode != 'EXPLICIT'
        self.inputs['Curve'].hide_safe = self.mode != 'CURVE'
        updateNode(self, context)

    mode : EnumProperty(
            name = "Curve Parameters",
            items = modes,
            default = 'GUESS',
            update = update_sockets)

    degree : IntProperty(
            name = "Degree",
            default = 3,
            min = 1,
            update = updateNode)

    n_cpts : IntProperty(
            name = "N Control Points",
            default = 4,
            min = 2,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Goals")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.inputs.new('SvStringsSocket', "NControlPoints").prop_name = 'n_cpts'
        self.inputs.new('SvStringsSocket', "Knotvector")
        self.inputs.new('SvStringsSocket', "CurveWeights")
        self.inputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvCurveSocket', "Curve")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        # Expect list of lists of lists of goals; we convert each list of goals into one curve.
        goals_s = self.inputs['Goals'].sv_get() 
        goals_s = ensure_nesting_level(goals_s, 3, data_types=(SvNurbsCurveGoal,))
        degree_s = self.inputs['Degree'].sv_get() # expect list of lists of numbers -> list of lists of curves
        degree_s = ensure_nesting_level(degree_s, 2)
        if self.mode == 'EXPLICIT':
            # a number for each curve
            n_cpts_s = self.inputs['NControlPoints'].sv_get()
            n_cpts_s = ensure_nesting_level(n_cpts_s, 2)
            # list of numbers for each curve
            knotvector_s = self.inputs['Knotvector'].sv_get(default=[[None]])
            if self.inputs['Knotvector'].is_linked:
                knotvector_s = ensure_nesting_level(knotvector_s, 3)
            # list of numbers for each curve
            weights_s = self.inputs['CurveWeights'].sv_get(default=[[None]])
            if self.inputs['CurveWeights'].is_linked:
                weights_s = ensure_nesting_level(weights_s, 3)
            curves_s = [[None]]
        elif self.mode == 'CURVE':
            # a number for each curve
            n_cpts_s = [[None]]
            # list of numbers for each curve
            knotvector_s = [[None]]
            # list of numbers for each curve
            weights_s = [[None]]
            curves_s = self.inputs['Curve'].sv_get()
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
        else: # GUESS
            # a number for each curve
            n_cpts_s = [[None]]
            # list of numbers for each curve
            knotvector_s = [[None]]
            # list of numbers for each curve
            weights_s = [[None]]
            curves_s = [[None]]

        curves_out = []
        for params in zip_long_repeat(goals_s, degree_s, n_cpts_s, knotvector_s, weights_s, curves_s):
            new_curves = []
            for goals, degree, n_cpts, knotvector, weights, curve in zip_long_repeat(*params):
                if self.mode == 'CURVE':
                    curve = SvNurbsCurve.to_nurbs(curve)
                    if curve is None:
                        raise Exception("One of curves is not NURBS")
                    degree = None
                print(f"Goals: {len(goals)}, degree: {degree}, KV: {knotvector}, Ws: {weights}, curve: {curve}")
                solver = SvNurbsCurveSolver(degree=degree, src_curve=curve)
                solver.set_goals(goals)
                if self.mode == 'GUESS':
                    solver.guess_curve_params()
                elif self.mode == 'EXPLICIT':
                    solver.set_curve_params(n_cpts, knotvector, weights)
                else: # CURVE
                    n_cpts = len(curve.get_control_points())
                    knotvector = curve.get_knotvector()
                    weights = curve.get_weights()
                    solver.set_curve_params(n_cpts, knotvector, weights)

                new_curve = solver.solve(logger=self.get_logger())
                new_curves.append(new_curve)
            curves_out.append(new_curves)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvNurbsCurveSolverNode)

def unregister():
    bpy.utils.unregister_class(SvNurbsCurveSolverNode)

