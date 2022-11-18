import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

class SvExSdfOrientNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF Orient
    Tooltip: SDF Orient
    """
    bl_idname = 'SvExSdfOrientNode'
    bl_label = 'SDF Orient'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_dependencies = {'sdf'}

    axis_v: FloatVectorProperty(
        name="Axis",
        default=(0, 0, 1),
        size=3,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvVerticesSocket', "Axis").prop_name = 'axis_v'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        axis_s = self.inputs['Axis'].sv_get()

        input_level = get_data_nesting_level(sdf_s, data_types=(SvScalarField,))
        flat_output = input_level == 1
        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        axis_s = ensure_nesting_level(axis_s, 3)

        sdf_out = []
        for params in zip_long_repeat(sdf_s, axis_s):
            new_sdf = []
            for sdf, axis in zip_long_repeat(*params):
                sdf = scalar_field_to_sdf(sdf, 0)
                sdf = sdf.orient(axis)
                field = SvExSdfScalarField(sdf)
                new_sdf.append(field)
            if flat_output:
                sdf_out.extend(new_sdf)
            else:
                sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)


def register():
    bpy.utils.register_class(SvExSdfOrientNode)


def unregister():
    bpy.utils.unregister_class(SvExSdfOrientNode)

