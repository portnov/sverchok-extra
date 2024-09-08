# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok_extra.dependencies import shapely

class SvExShapelyPolylineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Poly Line
    Tooltip: 2D Poly Line
    """
    bl_idname = "SvExShapelyPolylineNode"
    bl_label = "2D Polyline"
    sv_icon = 'SV_POLYLINE'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_dependencies = {'shapely'}

    cycle : BoolProperty(
            name = "Cycle",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'cycle')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_s = self.inputs['Vertices'].sv_get()
        verts_s = ensure_nesting_level(verts_s, 3)

        polygons_out = []
        for verts in verts_s:
            if self.cycle:
                polygon = shapely.LinearRing(verts)
            else:
                polygon = shapely.LineString(verts)
            polygons_out.append(polygon)

        self.outputs['Geometry'].sv_set(polygons_out)

def register():
    bpy.utils.register_class(SvExShapelyPolylineNode)


def unregister():
    bpy.utils.unregister_class(SvExShapelyPolylineNode)

