import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList

class SvExCurveTorsionNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Curve Torsion / Twist
        Tooltip: Calculate torsion of the curve at given parameter value
        """
        bl_idname = 'SvExCurveTorsionNode'
        bl_label = 'Curve Torsion'
        bl_icon = 'CURVE_NCURVE'

        def sv_init(self, context):
            self.inputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'
            self.inputs.new('SvStringsSocket', "T")
            self.outputs.new('SvStringsSocket', "Torsion")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            ts_s = self.inputs['T'].sv_get()

            twist_out = []
            for curve, ts in zip_long_repeat(curve_s, ts_s):
                ts = np.array(ts)
                twists = curve.twist_array(ts)
                twist_out.append(twists.tolist())

            self.outputs['Torsion'].sv_set(twist_out)

def register():
    bpy.utils.register_class(SvExCurveTorsionNode)

def unregister():
    bpy.utils.unregister_class(SvExCurveTorsionNode)

