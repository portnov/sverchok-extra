import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import *

class SvExSdfRoundedCylinderNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF Rounded Cylinder
    Tooltip: SDF Rounded Cylinder
    """
    bl_idname = 'SvExSdfRoundedCylinderNode'
    bl_label = 'SDF Rounded Cylinder'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_dependencies = {'sdf'}

    major_radius: FloatProperty(
        name="Major Radius",
        default=1,
        update=updateNode)

    minor_radius: FloatProperty(
        name="Minor Radius",
        default=0.2,
        update=updateNode)

    cyl_height: FloatProperty(
        name="Height",
        default=2,
        update=updateNode)

    origin: FloatVectorProperty(
        name="Origin",
        default=(0, 0, 0),
        size=3,
        update=updateNode)

    origin_at_center: BoolProperty(
        name = "Center",
        default = True,
        update=updateNode)

    flat_output : BoolProperty(
        name = "Flat output",
        default = True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'origin_at_center')
        layout.prop(self, 'flat_output')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "MajorRadius").prop_name = 'major_radius'
        self.inputs.new('SvStringsSocket', "MinorRadius").prop_name = 'minor_radius'
        self.inputs.new('SvStringsSocket', "Height").prop_name = 'cyl_height'
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        major_radius_s = self.inputs['MajorRadius'].sv_get()
        minor_radius_s = self.inputs['MinorRadius'].sv_get()
        height_s = self.inputs['Height'].sv_get()
        origins_s = self.inputs['Origin'].sv_get()

        major_radius_s = ensure_nesting_level(major_radius_s, 2)
        minor_radius_s = ensure_nesting_level(minor_radius_s, 2)
        height_s = ensure_nesting_level(height_s, 2)
        origins_s = ensure_nesting_level(origins_s, 3)

        fields_out = []
        for params in zip_long_repeat(major_radius_s, minor_radius_s, height_s, origins_s):
            new_fields = []
            for major_radius, minor_radius, height, origin in zip_long_repeat(*params):
                if not self.origin_at_center:
                    x0, y0, z0 = origin
                    origin = x0, y0, z0 + (height / 2.0)
                sdf = rounded_cylinder(major_radius, minor_radius, height).translate(origin)
                field = SvExSdfScalarField(sdf)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)


def register():
    bpy.utils.register_class(SvExSdfRoundedCylinderNode)


def unregister():
    bpy.utils.unregister_class(SvExSdfRoundedCylinderNode)
