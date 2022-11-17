import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import sphere

class SvExSdfSphereNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Sphere
    Tooltip: SDF Sphere
    """
    bl_idname = 'SvExSdfSphereNode'
    bl_label = 'SDF Sphere'
    bl_icon = 'MESH_UVSPHERE'
    sv_dependencies = {'sdf'}

    sphere_radius: FloatProperty(
        name="Radius",
        default=1,
        precision=4,
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
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'sphere_radius'
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        radiuses_s = self.inputs['Radius'].sv_get()
        origins_s = self.inputs['Origin'].sv_get()

        radiuses_s = ensure_nesting_level(radiuses_s, 2)
        origins_s = ensure_nesting_level(origins_s, 3)

        fields_out = []
        for params in zip_long_repeat(radiuses_s, origins_s):
            new_fields = []
            for radius, origin in zip_long_repeat(*params):
                sdf = sphere(radius, origin)
                field = SvExSdfScalarField(sdf)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)


def register():
    bpy.utils.register_class(SvExSdfSphereNode)


def unregister():
    bpy.utils.unregister_class(SvExSdfSphereNode)
