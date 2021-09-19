import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.dummy_nodes import add_dummy
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is None:
    add_dummy('SvExSdfRadialTransitionNode', "SDF Radial Transition", 'sdf')
else:
    from sdf import *

    class SvExSdfRadialTransitionNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: SDF Radial Transition
        Tooltip: SDF Radial Transition
        """
        bl_idname = 'SvExSdfRadialTransitionNode'
        bl_label = 'SDF Radial Transition'
        bl_icon = 'OUTLINER_OB_EMPTY'

        easing_mode : EnumProperty(
                name = "Easing",
                items = easing_options,
                default = easing_options[0][0],
                update = updateNode)

        radius1: FloatProperty(
            name="Radius1",
            default=0.0,
            update=updateNode)

        radius2: FloatProperty(
            name="Radius2",
            default=1.0,
            update=updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'easing_mode')

        def sv_init(self, context):
            self.inputs.new('SvScalarFieldSocket', "SDF1")
            self.inputs.new('SvScalarFieldSocket', "SDF2")
            self.inputs.new('SvStringsSocket', "Radius1").prop_name = 'radius1'
            self.inputs.new('SvStringsSocket', "Radius2").prop_name = 'radius2'
            self.outputs.new('SvScalarFieldSocket', "SDF")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            sdf1_s = self.inputs['SDF1'].sv_get()
            sdf2_s = self.inputs['SDF2'].sv_get()
            radius1_s = self.inputs['Radius1'].sv_get()
            radius2_s = self.inputs['Radius2'].sv_get()

            input_level = get_data_nesting_level(sdf1_s, data_types=(SvScalarField,))
            flat_output = input_level == 1
            sdf1_s = ensure_nesting_level(sdf1_s, 2, data_types=(SvScalarField,))
            sdf2_s = ensure_nesting_level(sdf2_s, 2, data_types=(SvScalarField,))
            radius1_s = ensure_nesting_level(radius1_s, 2)
            radius2_s = ensure_nesting_level(radius2_s, 2)

            easing_function = easing_dict[int(self.easing_mode)]

            sdf_out = []
            for params in zip_long_repeat(sdf1_s, sdf2_s, radius1_s, radius2_s):
                new_sdf = []
                for sdf1, sdf2, radius1, radius2 in zip_long_repeat(*params):
                    sdf1 = scalar_field_to_sdf(sdf1, 0)
                    sdf2 = scalar_field_to_sdf(sdf2, 0)
                    sdf = transition_radial(sdf1, sdf2, r0=radius1, r1=radius2, e=easing_function)
                    field = SvExSdfScalarField(sdf)
                    new_sdf.append(field)
                if flat_output:
                    sdf_out.extend(new_sdf)
                else:
                    sdf_out.append(new_sdf)

            self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfRadialTransitionNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfRadialTransitionNode)

