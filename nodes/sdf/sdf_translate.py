import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

class SvExSdfTranslateNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF Translate
    Tooltip: SDF Translate
    """
    bl_idname = 'SvExSdfTranslateNode'
    bl_label = 'SDF Translate'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_MOVE'
    sv_dependencies = {'sdf'}

    vector: FloatVectorProperty(
        name="Vector",
        default=(0, 0, 0),
        size=3,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvVerticesSocket', "Vector").prop_name = 'vector'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        origins_s = self.inputs['Vector'].sv_get()

        input_level = get_data_nesting_level(sdf_s, data_types=(SvScalarField,))
        flat_output = input_level == 1
        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        origins_s = ensure_nesting_level(origins_s, 3)

        sdf_out = []
        for params in zip_long_repeat(sdf_s, origins_s):
            new_sdf = []
            for sdf, origin in zip_long_repeat(*params):
                sdf = scalar_field_to_sdf(sdf, 0)
                sdf = sdf.translate(origin)
                field = SvExSdfScalarField(sdf)
                new_sdf.append(field)
            if flat_output:
                sdf_out.extend(new_sdf)
            else:
                sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfTranslateNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfTranslateNode)

