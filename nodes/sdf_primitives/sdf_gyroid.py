import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.dummy_nodes import add_dummy
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is None:
    add_dummy('SvExSdfGyroidNode', "SDF Gyroid", 'sdf')
else:
    from sdf import *

class SvExSdfGyroidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Gyroid
    Tooltip: SDF Gyroid
    """
    bl_idname = 'SvExSdfGyroidNode'
    bl_label = 'SDF Gyroid'
    bl_icon = 'MESH_CAPSULE'

    size_x : FloatProperty(
        name = "X Size",
        default = 1.0,
        min = 0.0,
        update=updateNode)

    size_y : FloatProperty(
        name = "Y Size",
        default = 1.0,
        min = 0.0,
        update=updateNode)

    size_z : FloatProperty(
        name = "Z Size",
        default = 1.0,
        min = 0.0,
        update=updateNode)

    thickness : FloatProperty(
        name = "Thickness",
        default = 0.1,
        min = 0.0,
        update=updateNode)

    value : FloatProperty(
        name = "Value",
        default = 0.0,
        min = 0.0,
        update=updateNode)

    origin: FloatVectorProperty(
        name="Origin",
        default=(0, 0, 0),
        size=3,
        update=updateNode)

    flat_output : BoolProperty(
        name = "Flat output",
        default = True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'flat_output')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "XSize").prop_name = 'size_x'
        self.inputs.new('SvStringsSocket', "YSize").prop_name = 'size_y'
        self.inputs.new('SvStringsSocket', "ZSize").prop_name = 'size_z'
        self.inputs.new('SvStringsSocket', "Thickness").prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', "Value").prop_name = 'value'
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        size_x_s = self.inputs['XSize'].sv_get()
        size_y_s = self.inputs['YSize'].sv_get()
        size_z_s = self.inputs['ZSize'].sv_get()
        thickness_s = self.inputs['Thickness'].sv_get()
        value_s = self.inputs['Value'].sv_get()
        origins_s = self.inputs['Origin'].sv_get()

        size_x_s = ensure_nesting_level(size_x_s, 2)
        size_y_s = ensure_nesting_level(size_y_s, 2)
        size_z_s = ensure_nesting_level(size_z_s, 2)
        thickness_s = ensure_nesting_level(thickness_s, 2)
        value_s = ensure_nesting_level(value_s, 2)
        origins_s = ensure_nesting_level(origins_s, 3)

        fields_out = []
        for params in zip_long_repeat(size_x_s, size_y_s, size_z_s, thickness_s, value_s, origins_s):
            new_fields = []
            for size_x, size_y, size_z, thickness, value, origin in zip_long_repeat(*params):
                sdf = gyroid(thickness, value, size=(size_x,size_y,size_z),center=origin).translate(origin)
                field = SvExSdfScalarField(sdf)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfGyroidNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfGyroidNode)
