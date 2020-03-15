
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level

from sverchok_extra.data.curve import SvExCurve, SvExGeomdlCurve
from sverchok_extra.dependencies import geomdl

if geomdl is not None:
    from geomdl import NURBS, BSpline, knotvector
    
    class SvExBlendCurvesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Blend curves NURBS
        Tooltip: Blend two curves by use of NURBS curve segment
        """
        bl_idname = 'SvExBlendCurvesNode'
        bl_label = 'Blend Curves by NURBS'
        bl_icon = 'CURVE_NCURVE'

        factor1 : FloatProperty(
            name = "Factor 1",
            default = 0.1,
            update = updateNode)

        factor2 : FloatProperty(
            name = "Factor 2",
            default = 0.1,
            update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvExCurveSocket', 'Curve1').display_shape = 'DIAMOND'
            self.inputs.new('SvExCurveSocket', 'Curve2').display_shape = 'DIAMOND'
            self.inputs.new('SvStringsSocket', "Factor1").prop_name = 'factor1'
            self.inputs.new('SvStringsSocket', "Factor2").prop_name = 'factor2'
            self.outputs.new('SvExCurveSocket', 'Curve').display_shape = 'DIAMOND'

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve1_s = self.inputs['Curve1'].sv_get()
            curve2_s = self.inputs['Curve2'].sv_get()
            factor1_s = self.inputs['Factor1'].sv_get()
            factor2_s = self.inputs['Factor2'].sv_get()

            if isinstance(curve1_s[0], SvExCurve):
                curve1_s = [curve1_s]
            if isinstance(curve2_s[0], SvExCurve):
                curve2_s = [curve2_s]
            factor1_s = ensure_nesting_level(factor1_s, 2)
            factor2_s = ensure_nesting_level(factor2_s, 2)

            curves_out = []
            for curve1s, curve2s, factor1s, factor2s in zip_long_repeat(curve1_s, curve2_s, factor1_s, factor2_s):
                for curve1, curve2, factor1, factor2 in zip_long_repeat(curve1s, curve2s, factor1s, factor2s):
                    _, t_max_1 = curve1.get_u_bounds()
                    t_min_2, _ = curve2.get_u_bounds()

                    curve1_end = curve1.evaluate(t_max_1)
                    curve2_begin = curve2.evaluate(t_min_2)
                    tangent_1_end = curve1.tangent(t_max_1)
                    tangent_2_begin = curve2.tangent(t_min_2)

                    tangent1 = factor1 * tangent_1_end / np.linalg.norm(tangent_1_end)
                    tangent2 = factor2 * tangent_2_begin / np.linalg.norm(tangent_2_begin)

                    new_curve = BSpline.Curve()
                    new_curve.degree = 3
                    ctrlpts =  [
                            curve1_end.tolist(), (curve1_end + tangent1).tolist(),
                            (curve2_begin - tangent2).tolist(), curve2_begin.tolist()
                        ]

                    new_curve.ctrlpts = ctrlpts
                    new_curve.knotvector = knotvector.generate(new_curve.degree, 4)
                    nurbs_curve = SvExGeomdlCurve(new_curve)
                    curves_out.append(nurbs_curve)

            self.outputs['Curve'].sv_set(curves_out)

def register():
    if geomdl is not None:
        bpy.utils.register_class(SvExBlendCurvesNode)

def unregister():
    if geomdl is not None:
        bpy.utils.unregister_class(SvExBlendCurvesNode)

