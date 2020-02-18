
import numpy as np

from mathutils import Matrix
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList

from sverchok_extra.data.curve import SvExCircle

class SvExCircleNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Circle
    Tooltip: Generate circular curve
    """
    bl_idname = 'SvExLineCurveNode'
    bl_label = 'Circle (Curve)'
    bl_icon = 'MESH_CIRCLE'

    radius : FloatProperty(
        name = "Radius",
        default = 1.0,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvMatrixSocket', "Center")
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.outputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get(default=[Matrix()])
        radius_s = self.inputs['Radius'].sv_get()

        curves_out = []
        for center, radius in zip_long_repeat(center_s, radius_s):
            if isinstance(radius, (list, tuple)):
                radius = radius[0]

            curve = SvExCircle(center, radius)
            curves_out.append(curve)

        self.outputs['Curve'].sv_set(curves_out)

def register():
    bpy.utils.register_class(SvExCircleNode)

def unregister():
    bpy.utils.unregister_class(SvExCircleNode)

