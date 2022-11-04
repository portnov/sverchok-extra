import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import *

class SvExSdfCylinderNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Cylinder
    Tooltip: SDF Cylinder
    """
    bl_idname = 'SvExSdfCylinderNode'
    bl_label = 'SDF Cylinder'
    bl_icon = 'MESH_CYLINDER'
    sv_dependencies = {'sdf'}

    cyl_radius: FloatProperty(
        name="Radius",
        default=1,
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
        default = False,
        update=updateNode)

    flat_output : BoolProperty(
        name = "Flat output",
        default = True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'origin_at_center')
        layout.prop(self, 'flat_output')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'cyl_radius'
        self.inputs.new('SvStringsSocket', "Height").prop_name = 'cyl_height'
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        radiuses_s = self.inputs['Radius'].sv_get()
        height_s = self.inputs['Height'].sv_get()
        origins_s = self.inputs['Origin'].sv_get()

        radiuses_s = ensure_nesting_level(radiuses_s, 2)
        height_s = ensure_nesting_level(height_s, 2)
        origins_s = ensure_nesting_level(origins_s, 3)

        fields_out = []
        for params in zip_long_repeat(radiuses_s, height_s, origins_s):
            new_fields = []
            for radius, height, origin in zip_long_repeat(*params):
                if self.origin_at_center:
                    x0, y0, z0 = origin
                    origin = x0, y0, z0 - (height / 2.0)
                sdf = capped_cylinder((0, 0, 0), (0, 0, height), radius).translate(origin)
                field = SvExSdfScalarField(sdf)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfCylinderNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfCylinderNode)

