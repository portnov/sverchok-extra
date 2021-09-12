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
    add_dummy('SvExSdfSliceNode', "SDF Slice", 'sdf')

class SvExSdfSliceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Slice
    Tooltip: SDF Slice
    """
    bl_idname = 'SvExSdfSliceNode'
    bl_label = 'SDF Slice'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SLICE_SOLID'

    z_value : FloatProperty(
            name = "Z Value",
            default = 0.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvStringsSocket', "ZValue").prop_name = 'z_value'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        z_value_s = self.inputs['ZValue'].sv_get()

        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        z_value_s = ensure_nesting_level(z_value_s, 2)

        sdf_out = []
        for params in zip_long_repeat(sdf_s, z_value_s):
            new_sdf = []
            for sdf, z_value in zip_long_repeat(*params):
                sdf = scalar_field_to_sdf(sdf, 0)
                sdf_2d = sdf.translate((0, 0, -z_value)).slice()
                field = SvExSdf2DScalarField(sdf_2d)
                new_sdf.append(field)
            sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfSliceNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfSliceNode)

