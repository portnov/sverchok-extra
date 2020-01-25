
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level

from sverchok_extra.data.field.vector import SvExBendAlongCurveField

class SvExBendAlongCurveFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bend Along Curve
    Tooltip: Bend Along Curve
    """
    bl_idname = 'SvExBendAlongCurveFieldNode'
    bl_label = 'Bend Along Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'

    algorithms = [
            ("householder", "Householder", "Use Householder reflection matrix", 1),
            ("track", "Tracking", "Use quaternion-based tracking", 2),
            ("diff", "Rotation difference", "Use rotational difference calculation", 3)
        ]

    algorithm: EnumProperty(
        name="Algorithm", description="Rotation calculation algorithm",
        default="householder", items=algorithms, update=updateNode)

    axes = [
            ("X", "X", "X axis", 1),
            ("Y", "Y", "Y axis", 2),
            ("Z", "Z", "Z axis", 3)
        ]

    orient_axis_: EnumProperty(
        name="Orientation axis", description="Which axis of object to put along path",
        default="Z", items=axes, update=updateNode)

    t_min : FloatProperty(
        name = "T Min",
        default = -1.0,
        update = updateNode)

    t_max : FloatProperty(
        name = "T Max",
        default = 1.0,
        update = updateNode)

    orient_axis_: EnumProperty(
        name="Orientation axis", description="Which axis of object to put along path",
        default="Z", items=axes, update=updateNode)

    def get_axis_idx(self, letter):
        return 'XYZ'.index(letter)

    def get_orient_axis_idx(self):
        return self.get_axis_idx(self.orient_axis_)

    orient_axis = property(get_orient_axis_idx)

    up_axis: EnumProperty(
        name="Up axis", description="Which axis of object should look up",
        default='X', items=axes, update=updateNode)

    scale_all: BoolProperty(
        name="Scale all axes", description="Scale objects along all axes or only along orientation axis",
        default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', 'Curve').display_shape = 'DIAMOND'
        self.inputs.new('SvStringsSocket', 'TMin').prop_name = 't_min'
        self.inputs.new('SvStringsSocket', 'TMax').prop_name = 't_max'
        self.outputs.new('SvExVectorFieldSocket', 'Field')

    def draw_buttons(self, context, layout):
        layout.label(text="Orientation:")
        layout.prop(self, "orient_axis_", expand=True)

        col = layout.column(align=True)
        col.prop(self, "scale_all", toggle=True)
        layout.prop(self, "algorithm")
        if self.algorithm == 'track':
            layout.prop(self, "up_axis")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get()
        t_min_s = self.inputs['TMin'].sv_get()
        t_max_s = self.inputs['TMax'].sv_get()

        fields_out = []
        for curve, t_min, t_max in zip_long_repeat(curves_s, t_min_s, t_max_s):
            if isinstance(t_min, (list, int)):
                t_min = t_min[0]
            if isinstance(t_max, (list, int)):
                t_max = t_max[0]

            field = SvExBendAlongCurveField(curve, self.algorithm, self.scale_all,
                        self.orient_axis, t_min, t_max, self.up_axis)
            fields_out.append(field)

        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvExBendAlongCurveFieldNode)

def unregister():
    bpy.utils.unregister_class(SvExBendAlongCurveFieldNode)

