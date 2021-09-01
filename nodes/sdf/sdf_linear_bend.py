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
    add_dummy('SvExSdfLinearBendNode', "SDF Linear Bend", 'sdf')

class SvExSdfLinearBendNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Linear Bend
    Tooltip: SDF Linear Bend
    """
    bl_idname = 'SvExSdfLinearBendNode'
    bl_label = 'SDF Linear Bend'
    bl_icon = 'OUTLINER_OB_EMPTY'

    easing_options = [(str(k), f.__name__, f.__name__, f.__name__, k) for k, f in easing_dict.items()]

    easing_mode : EnumProperty(
            name = "Easing",
            items = easing_options,
            default = easing_options[0][0],
            update = updateNode)

    point1 : FloatVectorProperty(
        name="Point1",
        default=(0, 0, -1),
        size=3,
        update=updateNode)

    point2 : FloatVectorProperty(
        name="Point2",
        default=(0, 0, 1),
        size=3,
        update=updateNode)

    vector : FloatVectorProperty(
        name="Vector",
        default=(1, 0, 0),
        size=3,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'easing_mode')

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvVerticesSocket', "Point1").prop_name = 'point1'
        self.inputs.new('SvVerticesSocket', "Point2").prop_name = 'point2'
        self.inputs.new('SvVerticesSocket', "Vector").prop_name = 'vector'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        point1_s = self.inputs['Point1'].sv_get()
        point2_s = self.inputs['Point2'].sv_get()
        vector_s = self.inputs['Vector'].sv_get()

        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        point1_s = ensure_nesting_level(point1_s, 3)
        point2_s = ensure_nesting_level(point2_s, 3)
        vector_s = ensure_nesting_level(vector_s, 3)

        easing_function = easing_dict[int(self.easing_mode)]

        sdf_out = []
        for params in zip_long_repeat(sdf_s, point1_s, point2_s, vector_s):
            new_sdf = []
            for sdf, point1, point2, vector in zip_long_repeat(*params):
                sdf = scalar_field_to_sdf(sdf, 0)

                sdf = sdf.bend_linear(p0=point1, p1=point2, v=vector, e=easing_function)

                field = SvExSdfScalarField(sdf)
                new_sdf.append(field)
            sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfLinearBendNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfLinearBendNode)

