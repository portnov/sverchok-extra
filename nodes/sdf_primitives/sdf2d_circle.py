import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import *

class SvExSdf2dCircleNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF 2D Circle
    Tooltip: SDF 2D Circle
    """
    bl_idname = 'SvExSdf2dCircleNode'
    bl_label = 'SDF 2D Circle'
    bl_icon = 'MESH_CIRCLE'
    sv_dependencies = {'sdf'}

    circle_radius : FloatProperty(
        name = "Radius",
        default = 1.0,
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

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'circle_radius'
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'flat_output')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        radius_s = self.inputs['Radius'].sv_get()
        origins_s = self.inputs['Origin'].sv_get()

        radius_s = ensure_nesting_level(radius_s, 2)
        origins_s = ensure_nesting_level(origins_s, 3)

        fields_out = []
        for params in zip_long_repeat(radius_s, origins_s):
            new_fields = []
            for radius, origin in zip_long_repeat(*params):
                origin = origin[0:2]
                sdf2d = circle(radius=radius, center=origin)

                field = SvExSdf2DScalarField(sdf2d)

                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdf2dCircleNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdf2dCircleNode)

