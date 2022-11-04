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

class SvExSdfDilateErodeNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Dilate / Erode
    Tooltip: SDF Dilate / Erode
    """
    bl_idname = 'SvExSdfDilateErodeNode'
    bl_label = 'SDF Dilate / Erode'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_dependencies = {'sdf'}

    k_value : FloatProperty(
            name = "K Value",
            default = 0.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvStringsSocket', "KValue").prop_name = 'k_value'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        ks_s = self.inputs['KValue'].sv_get()

        input_level = get_data_nesting_level(sdf_s, data_types=(SvScalarField,))
        flat_output = input_level == 1
        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        ks_s = ensure_nesting_level(ks_s, 2)

        sdf_out = []
        for params in zip_long_repeat(sdf_s, ks_s):
            new_sdf = []
            for sdf, k in zip_long_repeat(*params):
                sdf = scalar_field_to_sdf(sdf, 0)
                if k >= 0:
                    sdf = sdf.dilate(k)
                else:
                    sdf = sdf.erode(-k)
                field = SvExSdfScalarField(sdf)
                new_sdf.append(field)
            if flat_output:
                sdf_out.extend(new_sdf)
            else:
                sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfDilateErodeNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfDilateErodeNode)

