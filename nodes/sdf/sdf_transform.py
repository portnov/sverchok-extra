import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField, SvVectorScalarFieldComposition
from sverchok.utils.field.vector import SvVectorField, SvMatrixVectorField, SvAbsoluteVectorField
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import *

class SvExSdfTransformNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF General Transform
    Tooltip: SDF General Transform
    """
    bl_idname = 'SvExSdfTransformNode'
    bl_label = 'SDF General Transform'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_dependencies = {'sdf'}

    def update_sockets(self, context):
        self.inputs['TransformField'].hide_safe = self.input_mode != 'FIELD'
        self.inputs['TransformMatrix'].hide_safe = self.input_mode != 'MATRIX'
        updateNode(self, context)

    input_modes = [
            ('MATRIX', "Matrix", "Matrix", 0),
            ('FIELD', "Vector Field", "Vector Field", 1)
        ]

    input_mode : EnumProperty(
            name = "Input mode",
            items = input_modes,
            default = 'MATRIX',
            update = update_sockets)

    field_types = [
            ('RELATIVE', "Relative", "Relative", 0),
            ('ABSOLUTE', "Absolute", "Absolute", 1)
        ]

    field_type : EnumProperty(
            name = "Field type",
            items = field_types,
            default = 'RELATIVE',
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text='Transformation:')
        layout.prop(self, 'input_mode', text='')
        if self.input_mode == 'FIELD':
            layout.label(text="Field type:")
            layout.prop(self, 'field_type', text='')

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvVectorFieldSocket', "TransformField")
        self.inputs.new('SvMatrixSocket', 'TransformMatrix')
        self.outputs.new('SvScalarFieldSocket', "SDF")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        input_level = get_data_nesting_level(sdf1_s, data_types=(SvScalarField,))
        flat_output = input_level == 1
        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))

        if self.inputs['TransformField'].is_linked:
            vfield_s = self.inputs['TransformField'].sv_get()
            vfield_s = ensure_nesting_level(vfield_s, 2, data_types=(SvVectorField,))
        else:
            vfield_s = [[None]]

        if self.inputs['TransformMatrix'].is_linked:
            matrix_s = self.inputs['TransformMatrix'].sv_get()
            matrix_s = ensure_nesting_level(matrix_s, 2, data_types=(Matrix,))
        else:
            matrix_s = [[None]]

        sdf_out = []
        for params in zip_long_repeat(sdf_s, vfield_s, matrix_s):
            new_sdf = []
            for sdf, vfield, matrix in zip_long_repeat(*params):
                if self.input_mode == 'MATRIX':
                    transform = SvMatrixVectorField(matrix.inverted())
                    transform = SvAbsoluteVectorField(transform)
                else:
                    if self.field_type == 'RELATIVE':
                        transform = SvAbsoluteVectorField(vfield)
                    else:
                        transform = vfield

                field = SvVectorScalarFieldComposition(transform, sdf)
                new_sdf.append(field)
            if flat_output:
                sdf_out.extend(new_sdf)
            else:
                sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfTransformNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfTransformNode)

