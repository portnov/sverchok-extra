import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

class SvExSdfRevolveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Revolve
    Tooltip: SDF Revolve
    """
    bl_idname = 'SvExSdfRevolveNode'
    bl_label = 'SDF Revolve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_REVOLVE_FACE'
    sv_dependencies = {'sdf'}

    offset : FloatProperty(
            name = "Offset",
            default = 1.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvStringsSocket', "Offset").prop_name = 'offset'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        offset_s = self.inputs['Offset'].sv_get()

        input_level = get_data_nesting_level(sdf_s, data_types=(SvScalarField,))
        flat_output = input_level == 1
        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        offset_s = ensure_nesting_level(offset_s, 2)

        sdf_out = []
        for params in zip_long_repeat(sdf_s, offset_s):
            new_sdf = []
            for sdf, offset in zip_long_repeat(*params):
                sdf_2d = scalar_field_to_sdf_2d(sdf, 0)
                sdf = sdf_2d.revolve(offset)
                field = SvExSdfScalarField(sdf)
                new_sdf.append(field)
            if flat_output:
                sdf_out.extend(new_sdf)
            else:
                sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfRevolveNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfRevolveNode)

