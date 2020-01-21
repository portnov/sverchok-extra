
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.logging import info, exception

from sverchok_extra.data import (SvExScalarField, SvExVectorField,
            SvExVectorFieldBinOp, SvExVectorFieldMultipliedByScalar,
            SvExVectorFieldsLerp,
            SvExVectorFieldCrossProduct, SvExVectorFieldsScalarProduct,
            SvExVectorFieldNorm, SvExVectorFieldTangent, SvExVectorFieldCotangent,
            SvExVectorFieldComposition, SvExVectorScalarFieldComposition)

class Socket(object):
    def __init__(self, type, id, idx=None):
        self.type = type
        self.id = id
        self.idx = idx

inputs_registry = dict()
outputs_registry = dict()

V_FIELD_A = Socket("SvExVectorFieldSocket", "VFieldA")
V_FIELD_B =  Socket("SvExVectorFieldSocket", "VFieldB")
S_FIELD_B =  Socket("SvExScalarFieldSocket", "SFieldB")

V_FIELD_C = Socket("SvExVectorFieldSocket", "VFieldC")
S_FIELD_C = Socket("SvExScalarFieldSocket", "SFieldC")
V_FIELD_D = Socket("SvExVectorFieldSocket", "VFieldD")

for idx, socket in enumerate([V_FIELD_A, V_FIELD_B, S_FIELD_B]):
    socket.idx = idx
    inputs_registry[socket.id] = socket

for idx, socket in enumerate([V_FIELD_C, S_FIELD_C, V_FIELD_D]):
    socket.idx = idx
    outputs_registry[socket.id] = socket

operations = [
    ('ADD', "Add", lambda x,y : x+y, [("VFieldA", "A"), ("VFieldB", "B")], [("VFieldC", "Sum")]),
    ('SUB', "Sub", lambda x, y : x-y, [("VFieldA", "A"), ('VFieldB', "B")], [("VFieldC", "Difference")]),
    ('AVG', "Average", lambda x, y : (x+y)/2, [("VFieldA", "A"), ("VFieldB", "B")], [("VFieldC", "Average")]),
    ('DOT', "Scalar Product", None, [("VFieldA", "A"), ("VFieldB", "B")], [("SFieldC", "Product")]),
    ('CROSS', "Vector Product", None, [("VFieldA", "A"), ("VFieldB","B")], [("VFieldC", "Product")]),
    ('MUL', "Multiply Scalar", None, [("VFieldA", "VField"), ("SFieldB", "Scalar")], [("VFieldC", "Product")]),
    ('TANG', "Projection decomposition", None, [("VFieldA", "VField"), ("VFieldB","Basis")], [("VFieldC", "Projection"), ("VFieldD", "Coprojection")]),
    ('COMPOSE', "Composition VB(VA(x))", None, [("VFieldA", "VA"), ("VFieldB", "VB")], [("VFieldC", "VC")]),
    ('COMPOSES', "Composition SB(VA(x))", None, [("VFieldA", "VA"), ("SFieldB", "SB")], [("SFieldC", "SC")]),
    ('NORM', "Norm", None, [("VFieldA", "VField")], [("SFieldC", "Norm")]),
    ('LERP', "Lerp A -> B", None, [("VFieldA", "A"), ("VFieldB", "B"), ("SFieldB", "Coefficient")], [("VFieldC", "VField")]),
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

def get_input_by_idx(idx):
    for socket in inputs_registry.values():
        if socket.idx == idx:
            return socket
    raise Exception("unsupported input idx")
    
def get_output_by_idx(idx):
    for socket in outputs_registry.values():
        if socket.idx == idx:
            return socket
    raise Exception("unsupported output idx")

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
        actual_inputs = dict(actual_inputs)
        actual_outputs = dict(actual_outputs)
        for socket in self.inputs:
            registered = get_input_by_idx(socket.index)
            socket.hide_safe = registered.id not in actual_inputs
            if not socket.hide_safe:
                socket.name = actual_inputs[registered.id]

        for socket in self.outputs:
            registered = get_output_by_idx(socket.index)
            socket.hide_safe = registered.id not in actual_outputs
            if not socket.hide_safe:
                socket.name = actual_outputs[registered.id]

    operation : EnumProperty(
        name = "Operation",
        items = operation_modes,
        default = 'ADD',
        update = update_sockets)

    def sv_init(self, context):
        for socket in inputs_registry:
            self.inputs.new(socket.type, socket.id).display_shape = 'CIRCLE_DOT'
        for socket in outputs_registry:
            self.outputs.new(socket.type, socket.id).display_shape = 'CIRCLE_DOT'
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vfield_a_s = self.inputs[V_FIELD_A.idx].sv_get()
        vfield_b_s = self.inputs[V_FIELD_B.idx].sv_get(default=[[None]])
        sfield_b_s = self.inputs[S_FIELD_B.idx].sv_get(default=[[None]])

        vfields_c_out = []
        vfields_d_out = []
        sfields_out = []
        for vfields_a, vfields_b, sfields_b in zip_long_repeat(vfield_a_s, vfield_b_s, sfield_b_s):

            if not isinstance(vfields_a, (list, tuple)):
                vfields_a = [vfields_a]
            if not isinstance(vfields_b, (list, tuple)):
                vfields_b = [vfields_b]
            if not isinstance(sfields_b, (list, tuple)):
                sfields_b = [sfields_b]

            for vfield_a, vfield_b, sfield_b in zip_long_repeat(vfields_a, vfields_b, sfields_b):

                inputs = dict(VFieldA = vfield_a, VFieldB = vfield_b, SFieldB = sfield_b)

                if self.operation == 'MUL':
                    field_c = SvExVectorFieldMultipliedByScalar(vfield_a, sfield_b)
                    vfields_c_out.append(field_c)
                elif self.operation == 'DOT':
                    field_c = SvExVectorFieldsScalarProduct(vfield_a, vfield_b)
                    sfields_out.append(field_c)
                elif self.operation == 'CROSS':
                    field_c = SvExVectorFieldCrossProduct(vfield_a, vfield_b)
                    vfields_c_out.append(field_c)
                elif self.operation == 'NORM':
                    field_c = SvExVectorFieldNorm(vfield_a)
                    sfields_out.append(field_c)
                elif self.operation == 'TANG':
                    field_c = SvExVectorFieldTangent(vfield_a, vfield_b)
                    field_d = SvExVectorFieldCotangent(vfield_a, vfield_b)
                    vfields_c_out.append(field_c)
                    vfields_d_out.append(field_d)
                elif self.operation == 'COMPOSE':
                    field_c = SvExVectorFieldComposition(vfield_a, vfield_b)
                    vfields_c_out.append(field_c)
                elif self.operation == 'COMPOSES':
                    field_c = SvExVectorScalarFieldComposition(vfield_a, sfield_b)
                    sfields_out.append(field_c)
                elif self.operation == 'LERP':
                    field_c = SvExVectorFieldsLerp(vfield_a, vfield_b, sfield_b)
                    vfields_c_out.append(field_c)
                else:
                    operation = get_operation(self.operation)
                    field_c = SvExVectorFieldBinOp(vfield_a, vfield_b, operation)
                    vfields_c_out.append(field_c)

        self.outputs[V_FIELD_C.idx].sv_set(vfields_c_out)
        self.outputs[V_FIELD_D.idx].sv_set(vfields_d_out)
        self.outputs[S_FIELD_C.idx].sv_set(sfields_out)

def register():
    bpy.utils.register_class(SvExVectorFieldMathNode)

def unregister():
    bpy.utils.unregister_class(SvExVectorFieldMathNode)

