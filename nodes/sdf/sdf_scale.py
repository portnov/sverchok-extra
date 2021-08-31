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
    add_dummy('SvExSdfScaleNode', "SDF Scale", 'sdf')

class SvExSdfScaleNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Scale
    Tooltip: SDF Scale
    """
    bl_idname = 'SvExSdfScaleNode'
    bl_label = 'SDF Scale'
    bl_icon = 'OUTLINER_OB_EMPTY'

    scale_v: FloatVectorProperty(
        name="Scale",
        default=(1, 1, 1),
        size=3,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvVerticesSocket', "Scale").prop_name = 'scale_v'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        scale_s = self.inputs['Scale'].sv_get()

        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        scale_s = ensure_nesting_level(scale_s, 3)

        sdf_out = []
        for params in zip_long_repeat(sdf_s, scale_s):
            new_sdf = []
            for sdf, scale in zip_long_repeat(*params):
                sdf = scalar_field_to_sdf(sdf, 0)
                sdf = sdf.scale(scale)
                field = SvExSdfScalarField(sdf)
                new_sdf.append(field)
            sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfScaleNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfScaleNode)

