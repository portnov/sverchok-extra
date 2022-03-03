import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.dummy_nodes import add_dummy
#from sverchok.utils.sv_easing_functions import easing_dict
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is None:
    add_dummy('SvExSdfLinearTransitionNode', "SDF Linear Transition", 'sdf')
else:
    from sdf import *

    class SvExSdfLinearTransitionNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: SDF Linear Transition
        Tooltip: SDF Linear Transition
        """
        bl_idname = 'SvExSdfLinearTransitionNode'
        bl_label = 'SDF Linear Transition'
        bl_icon = 'OUTLINER_OB_EMPTY'

        easing_mode : EnumProperty(
                name = "Easing",
                items = easing_options,
                default = easing_options[0][0],
                update = updateNode)

        point1: FloatVectorProperty(
            name="Point1",
            default=(0, 0, -1),
            size=3,
            update=updateNode)

        point2: FloatVectorProperty(
            name="Point2",
            default=(0, 0, 1),
            size=3,
            update=updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'easing_mode')

        def sv_init(self, context):
            self.inputs.new('SvScalarFieldSocket', "SDF1")
            self.inputs.new('SvScalarFieldSocket', "SDF2")
            self.inputs.new('SvVerticesSocket', "Point1").prop_name = 'point1'
            self.inputs.new('SvVerticesSocket', "Point2").prop_name = 'point2'
            self.outputs.new('SvScalarFieldSocket', "SDF")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            sdf1_s = self.inputs['SDF1'].sv_get()
            sdf2_s = self.inputs['SDF2'].sv_get()
            point1_s = self.inputs['Point1'].sv_get()
            point2_s = self.inputs['Point2'].sv_get()

            input_level = get_data_nesting_level(sdf1_s, data_types=(SvScalarField,))
            flat_output = input_level == 1
            sdf1_s = ensure_nesting_level(sdf1_s, 2, data_types=(SvScalarField,))
            sdf2_s = ensure_nesting_level(sdf2_s, 2, data_types=(SvScalarField,))
            point1_s = ensure_nesting_level(point1_s, 3)
            point2_s = ensure_nesting_level(point2_s, 3)

            easing_function = easing_dict[int(self.easing_mode)]

            sdf_out = []
            for params in zip_long_repeat(sdf1_s, sdf2_s, point1_s, point2_s):
                new_sdf = []
                for sdf1, sdf2, point1, point2 in zip_long_repeat(*params):
                    sdf1 = scalar_field_to_sdf(sdf1, 0)
                    sdf2 = scalar_field_to_sdf(sdf2, 0)
                    sdf = transition_linear(sdf1, sdf2, p0=point1, p1=point2, e=easing_function)
                    field = SvExSdfScalarField(sdf)
                    new_sdf.append(field)
                if flat_output:
                    sdf_out.extend(new_sdf)
                else:
                    sdf_out.append(new_sdf)

            self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfLinearTransitionNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfLinearTransitionNode)
