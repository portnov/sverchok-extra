import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import *

class SvExSdf2dPolygonNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF 2D Polygon
    Tooltip: SDF 2D Polygon
    """
    bl_idname = 'SvExSdf2dPolygonNode'
    bl_label = 'SDF 2D Polygon'
    bl_icon = 'RNDCURVE'
    sv_icon = 'SV_NGON'
    sv_dependencies = {'sdf'}

    flat_output : BoolProperty(
        name = "Flat output",
        default = True,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'flat_output')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_s = self.inputs['Vertices'].sv_get()

        verts_s = ensure_nesting_level(verts_s, 4)

        fields_out = []
        for params in verts_s:
            new_fields = []
            for verts in params:
                verts = [v[0:2] for v in verts]
                sdf2d = polygon(verts)

                field = SvExSdf2DScalarField(sdf2d)

                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)


def register():
    bpy.utils.register_class(SvExSdf2dPolygonNode)


def unregister():
    bpy.utils.unregister_class(SvExSdf2dPolygonNode)
