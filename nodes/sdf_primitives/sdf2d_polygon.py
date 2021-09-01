import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.dummy_nodes import add_dummy
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is None:
    add_dummy('SvExSdf2dPolygonNode', "SDF 2D Polygon", 'sdf')
else:
    from sdf import *

class SvExSdf2dPolygonNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF 2D Polygon
    Tooltip: SDF 2D Polygon
    """
    bl_idname = 'SvExSdf2dPolygonNode'
    bl_label = 'SDF 2D Polygon'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvScalarFieldSocket', "SDF")

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
            fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdf2dPolygonNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdf2dPolygonNode)

