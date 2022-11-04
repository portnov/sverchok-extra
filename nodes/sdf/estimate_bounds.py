import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

class SvExSdfEstimateBoundsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Estimate Scalar Field Bounds
    Tooltip: Estimate Scalar Field Bounds
    """
    bl_idname = 'SvExSdfEstimateBoundsNode'
    bl_label = 'Estimate Scalar Field Bounds'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_BOUNDING_BOX'
    sv_dependencies = {'sdf'}

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.outputs.new('SvVerticesSocket', "Bounds")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        fields_s = self.inputs['Field'].sv_get()
        fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
        bounds_out = []
        for fields in fields_s:
            for field in fields:
                bounds = estimate_bounds(field)
                bounds_out.append(bounds)

        self.outputs['Bounds'].sv_set(bounds_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfEstimateBoundsNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfEstimateBoundsNode)

