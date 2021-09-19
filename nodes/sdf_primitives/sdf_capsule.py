import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.dummy_nodes import add_dummy
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is None:
    add_dummy('SvExSdfCapsuleNode', "SDF Capsule", 'sdf')
else:
    from sdf import *

class SvExSdfCapsuleNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Capsule
    Tooltip: SDF Capsule
    """
    bl_idname = 'SvExSdfCapsuleNode'
    bl_label = 'SDF Capsule'
    bl_icon = 'MESH_CAPSULE'

    caps_radius : FloatProperty(
        name="Radius",
        default=0.5,
        update=updateNode)

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

    flat_output : BoolProperty(
        name = "Flat output",
        default = True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'flat_output')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'caps_radius'
        self.inputs.new('SvVerticesSocket', "Point1").prop_name = 'point1'
        self.inputs.new('SvVerticesSocket', "Point2").prop_name = 'point2'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        radiuses_s = self.inputs['Radius'].sv_get()
        point1_s = self.inputs['Point1'].sv_get()
        point2_s = self.inputs['Point2'].sv_get()

        radiuses_s = ensure_nesting_level(radiuses_s, 2)
        point1_s = ensure_nesting_level(point1_s, 3)
        point2_s = ensure_nesting_level(point2_s, 3)

        fields_out = []
        for params in zip_long_repeat(radiuses_s, point1_s, point2_s):
            new_fields = []
            for radius, point1, point2 in zip_long_repeat(*params):
                sdf = capsule(point1, point2, radius)
                field = SvExSdfScalarField(sdf)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfCapsuleNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfCapsuleNode)

