import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import *

class SvExSdfBlendNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF Blend
    Tooltip: SDF Blend
    """
    bl_idname = 'SvExSdfBlendNode'
    bl_label = 'SDF Blend'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MIX_INPUTS'
    sv_dependencies = {'sdf'}

    k_value : FloatProperty(
            name = "K Value",
            default = 0.5,
            min = 0.0,
            max = 1.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF1")
        self.inputs.new('SvScalarFieldSocket', "SDF2")
        self.inputs.new('SvStringsSocket', "KValue").prop_name = 'k_value'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf1_s = self.inputs['SDF1'].sv_get()
        sdf2_s = self.inputs['SDF2'].sv_get()
        ks_s = self.inputs['KValue'].sv_get()

        input_level = get_data_nesting_level(sdf1_s, data_types=(SvScalarField,))
        flat_output = input_level == 1
        sdf1_s = ensure_nesting_level(sdf1_s, 2, data_types=(SvScalarField,))
        sdf2_s = ensure_nesting_level(sdf2_s, 2, data_types=(SvScalarField,))
        ks_s = ensure_nesting_level(ks_s, 2)

        sdf_out = []
        for params in zip_long_repeat(sdf1_s, sdf2_s, ks_s):
            new_sdf = []
            for sdf1, sdf2, k in zip_long_repeat(*params):
                sdf1 = scalar_field_to_sdf(sdf1, 0)
                sdf2 = scalar_field_to_sdf(sdf2, 0)
                sdf = blend(sdf1, sdf2, k=k)
                field = SvExSdfScalarField(sdf)
                new_sdf.append(field)
            if flat_output:
                sdf_out.extend(new_sdf)
            else:
                sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfBlendNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfBlendNode)

