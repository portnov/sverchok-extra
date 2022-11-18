import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import *

class SvExSdfPlatonicSolidNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF Platonic Solid
    Tooltip: SDF Platonic Solid
    """
    bl_idname = 'SvExSdfPlatonicSolidNode'
    bl_label = 'SDF Platonic Solid'
    bl_icon = 'GRIP'
    sv_icon = 'SV_REGULAR_SOLID'
    sv_dependencies = {'sdf'}

    s_radius : FloatProperty(
        name = "Radius",
        default = 1.0,
        min = 0.0,
        update=updateNode)

    origin: FloatVectorProperty(
        name="Origin",
        default=(0, 0, 0),
        size=3,
        update=updateNode)

    solid_types = [
            ('TETRA', "Tetrahedron", "Tetrahedron", 0),
            ('CUBE', "Cube", "Cube", 1),
            ('OCTA', "Octahedron", "Octahedron", 2),
            ('DODECA', "Dodecahedron", "Dodecahedron", 3),
            ('ICOSA', "Icosahedron", "Icosahedron", 4)
        ]

    solid_type : EnumProperty(
        name = "Solid type",
        items = solid_types,
        default = 'TETRA',
        update = updateNode)

    flat_output : BoolProperty(
        name = "Flat output",
        default = True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'solid_type')
        layout.prop(self, 'flat_output')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 's_radius'
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
        self.outputs.new('SvScalarFieldSocket', "SDF")

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
            for radius, origin, in zip_long_repeat(*params):
                if self.solid_type == 'TETRA':
                    sdf = tetrahedron(radius).translate(origin)
                elif self.solid_type == 'CUBE':
                    sdf = box(2*radius).translate(origin)
                elif self.solid_type == 'OCTA':
                    sdf = octahedron(radius).translate(origin)
                elif self.solid_type == 'DODECA':
                    sdf = dodecahedron(radius).translate(origin)
                else: # ICOSA
                    sdf = icosahedron(radius).translate(origin)
                field = SvExSdfScalarField(sdf)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfPlatonicSolidNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfPlatonicSolidNode)

