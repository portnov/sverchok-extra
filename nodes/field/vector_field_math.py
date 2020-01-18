
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.modules.eval_formula import get_variables, safe_eval
from sverchok.utils.logging import info, exception

from sverchok_extra.data import SvExVectorFieldBinOp, SvExVectorFieldMultipliedByScalar, SvExVectorFieldCrossProduct

def add(x,y):
    r = x+y
    return r

operations = [
    ('ADD', "Add", add, ["VFieldA", "VFieldB"], ["VFieldC"]),
    ('SUB', "Sub", lambda x, y : x-y, ["VFieldA", 'VFieldB'], ["VFieldC"]),
    ('AVG', "Average", lambda x, y : (x+y)/2, ["VFieldA", "VFieldB"], ["VFieldC"]),
    ('DOT', "Scalar Product", lambda x, y : x.dot(y), ["VFieldA", "VFieldB"], ["SFieldC"]),
    ('CROSS', "Vector Product", lambda x, y : np.cross(x, y), ["VFieldA", "VFieldB"], ["VFieldC"]),
    ('MUL', "Multiply Scalar", lambda x, y : x * y, ["VFieldA", "SFieldB"], ["VFieldC"])
]

operation_modes = [ (id, name, name, i) for i, (id, name, fn, _, _) in enumerate(operations) ]

def get_operation(op_id):
    for id, _, function, _, _ in operations:
        if id == op_id:
            return function
    raise Exception("Unsupported operation: " + op_id)

def get_sockets(op_id):
    actual_inputs = None
    actual_outputs = None
    for id, _, _, inputs, outputs in operations:
        if id == op_id:
            return inputs, outputs
    raise Exception("unsupported operation")

def vectorize(operation):
    def go(X, Y):
        xs1, ys1, zs1 = X
        xs2, ys2, zs2 = Y
        X1 = np.vstack((xs1, ys1, zs1))
        Y1 = np.vstack((xs2, ys2, zs2))
        R = operation(X1, Y1)
        return R[0,:,:][np.newaxis], R[1,:,:][np.newaxis], R[2,:,:][np.newaxis]
#         X1 = np.stack((xs1, ys1, zs1)).T
#         Y1 = np.stack((xs2, ys2, zs2)).T
#         R = operation(X1, Y1)
#         return R[:,:,:,0].T, R[:,:,:,1].T, R[:,:,:,2].T
    return go

class SvExVectorFieldMathNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Vector Field Math
    Tooltip: Vector Field Math
    """
    bl_idname = 'SvExVectorFieldMathNode'
    bl_label = 'Vector Field Math'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    @throttled
    def update_sockets(self, context):
        actual_inputs, actual_outputs = get_sockets(self.operation)
        for socket in self.inputs:
            socket.hide_safe = socket.name not in actual_inputs
        for socket in self.outputs:
            socket.hide_safe = socket.name not in actual_outputs

    operation : EnumProperty(
        name = "Operation",
        items = operation_modes,
        default = 'ADD',
        update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvExVectorFieldSocket', "VFieldA").display_shape = 'CIRCLE_DOT'
        self.inputs.new('SvExVectorFieldSocket', "VFieldB").display_shape = 'CIRCLE_DOT'
        self.inputs.new('SvExScalarFieldSocket', "SFieldB").display_shape = 'CIRCLE_DOT'
        self.outputs.new('SvExVectorFieldSocket', "VFieldC").display_shape = 'CIRCLE_DOT'
        self.outputs.new('SvExScalarFieldSocket', "SFieldC").display_shape = 'CIRCLE_DOT'
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vfield_a_s = self.inputs['VFieldA'].sv_get()
        vfield_b_s = self.inputs['VFieldB'].sv_get(default=[None])
        sfield_b_s = self.inputs['SFieldB'].sv_get(default=[None])

        vfields_out = []
        sfields_out = []
        for vfield_a, vfield_b, sfield_b in zip_long_repeat(vfield_a_s, vfield_b_s, sfield_b_s):
            inputs = dict(VFieldA = vfield_a, VFieldB = vfield_b, SFieldB = sfield_b)
            outputs = dict(VFieldC = vfields_out, SFieldC = sfields_out)

            actual_inputs, actual_outputs = get_sockets(self.operation)
            operation = get_operation(self.operation)

            if self.operation == 'MUL':
                field_c = SvExVectorFieldMultipliedByScalar(vfield_a, sfield_b)
            elif self.operation == 'CROSS':
                field_c = SvExVectorFieldCrossProduct(vfield_a, vfield_b)
            else:
                field_c = SvExVectorFieldBinOp(inputs[actual_inputs[0]], inputs[actual_inputs[1]], vectorize(operation))
            outputs[actual_outputs[0]].append(field_c)

        self.outputs['VFieldC'].sv_set(vfields_out)
        self.outputs['SFieldC'].sv_set(sfields_out)

def register():
    bpy.utils.register_class(SvExVectorFieldMathNode)

def unregister():
    bpy.utils.unregister_class(SvExVectorFieldMathNode)

