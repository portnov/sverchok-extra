import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import torus

class SvExSdfTorusNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Torus
    Tooltip: SDF Torus
    """
    bl_idname = 'SvExSdfTorusNode'
    bl_label = 'SDF Torus'
    bl_icon = 'MESH_TORUS'
    sv_dependencies = {'sdf'}

    major_radius : FloatProperty(
        name="Major Radius",
        min = 0.0,
        default=2,
        update=updateNode)

    minor_radius : FloatProperty(
        name="Minor Radius",
        min = 0.0,
        default=0.5,
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
        self.inputs.new('SvStringsSocket', "MajorRadius").prop_name = 'major_radius'
        self.inputs.new('SvStringsSocket', "MinorRadius").prop_name = 'minor_radius'
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        major_radius_s = self.inputs['MajorRadius'].sv_get()
        minor_radius_s = self.inputs['MinorRadius'].sv_get()
        origins_s = self.inputs['Origin'].sv_get()

        major_radius_s = ensure_nesting_level(major_radius_s, 2)
        minor_radius_s = ensure_nesting_level(minor_radius_s, 2)
        origins_s = ensure_nesting_level(origins_s, 3)

        fields_out = []
        for params in zip_long_repeat(major_radius_s, minor_radius_s, origins_s):
            new_fields = []
            for major_radius, minor_radius, origin in zip_long_repeat(*params):
                sdf = torus(major_radius, minor_radius).translate(origin)
                field = SvExSdfScalarField(sdf)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfTorusNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfTorusNode)

