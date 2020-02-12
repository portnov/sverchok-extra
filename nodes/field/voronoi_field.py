import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import kdtree
from mathutils import bvhtree

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.logging import info, exception

from sverchok_extra.data.field.scalar import SvExVoronoiScalarField

class SvExVoronoiFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Voronoi Field
    Tooltip: Generate Voronoi field
    """
    bl_idname = 'SvExVoronoiFieldNode'
    bl_label = 'Voronoi Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvExScalarFieldSocket', "Field").display_shape = 'CIRCLE_DOT'

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()

        fields_out = []
        for vertices in vertices_s:
            field = SvExVoronoiScalarField(vertices)
            fields_out.append(field)

        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvExVoronoiFieldNode)

def unregister():
    bpy.utils.unregister_class(SvExVoronoiFieldNode)

