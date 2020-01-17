
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.modules.eval_formula import get_variables, safe_eval
from sverchok.utils.logging import info, exception

from sverchok_extra.data import SvExScalarFieldBinOp

operations = [
    ('ADD', "Add", lambda x, y : x+y),
    ('SUB', "Sub", lambda x, y : x-y),
    ('MUL', "Multiply", lambda x, y : x * y),
    ('MIN', "Minimum", lambda x, y : np.min([x,y],axis=0)),
    ('MAX', "Maximum", lambda x, y : np.max([x,y],axis=0)),
    ('AVG', "Average", lambda x, y : (x+y)/2)
]

operation_modes = [ (id, name, name, i) for i, (id, name, fn) in enumerate(operations) ]

def get_operation(op_id):
    for id, _, function in operations:
        if id == op_id:
            return function
    raise Exception("Unsupported operation: " + op_id)

class SvExScalarFieldMathNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Scalar Field Math
    Tooltip: Scalar Field Math
    """
    bl_idname = 'SvExScalarFieldMathNode'
    bl_label = 'Scalar Field Math'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    operation : EnumProperty(
        name = "Operation",
        items = operation_modes,
        default = 'ADD',
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvExScalarFieldSocket', "FieldA").display_shape = 'CIRCLE_DOT'
        self.inputs.new('SvExScalarFieldSocket', "FieldB").display_shape = 'CIRCLE_DOT'
        self.outputs.new('SvExScalarFieldSocket', "FieldC").display_shape = 'CIRCLE_DOT'

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        field_a_s = self.inputs['FieldA'].sv_get()
        field_b_s = self.inputs['FieldB'].sv_get()

        fields_out = []
        for field_a, field_b in zip_long_repeat(field_a_s, field_b_s):
            operation = get_operation(self.operation)
            field_c = SvExScalarFieldBinOp(field_a, field_b, operation)
            fields_out.append(field_c)

        self.outputs['FieldC'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvExScalarFieldMathNode)

def unregister():
    bpy.utils.unregister_class(SvExScalarFieldMathNode)

