import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.dummy_nodes import add_dummy
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is None:
    add_dummy('SvExSdfBooleanNode', "SDF Boolean", 'sdf')
else:
    from sdf import sphere

class SvExSdfBooleanNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Boolean
    Tooltip: SDF Boolean
    """
    bl_idname = 'SvExSdfBooleanNode'
    bl_label = 'SDF Boolean'
    bl_icon = 'OUTLINER_OB_EMPTY'

    operations = [
            ('UNION', "Union", "Union", 0),
            ('INTERSECTION', "Intersection", "Intersection", 1),
            ('DIFFERENCE', "Difference", "Difference", 2)
        ]

    operation : EnumProperty(
            name = "Operation",
            items = operations,
            default = 'UNION',
            update = updateNode)

    k_value : FloatProperty(
            name = "K Value",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF1")
        self.inputs.new('SvScalarFieldSocket', "SDF2")
        self.inputs.new('SvStringsSocket', "KValue").prop_name = 'k_value'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf1_s = self.inputs['SDF1'].sv_get()
        sdf2_s = self.inputs['SDF2'].sv_get()
        ks_s = self.inputs['KValue'].sv_get()

        sdf1_s = ensure_nesting_level(sdf1_s, 2, data_types=(SvScalarField,))
        sdf2_s = ensure_nesting_level(sdf2_s, 2, data_types=(SvScalarField,))
        ks_s = ensure_nesting_level(ks_s, 2)

        sdf_out = []
        for params in zip_long_repeat(sdf1_s, sdf2_s, ks_s):
            new_sdf = []
            for sdf1, sdf2, k in zip_long_repeat(*params):
                sdf1 = scalar_field_to_sdf(sdf1, 0)
                sdf2 = scalar_field_to_sdf(sdf2, 0)
                print("Sdf", sdf1, sdf2)
                if self.operation == 'UNION':
                    sdf = union(sdf1, sdf2, k=k)
                elif self.operation == 'INTERSECTION':
                    sdf = intersection(sdf1, sdf2, k=k)
                else:
                    sdf = difference(sdf1, sdf2, k=k)
                field = SvExSdfScalarField(sdf)
                new_sdf.append(field)
            sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfBooleanNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfBooleanNode)
