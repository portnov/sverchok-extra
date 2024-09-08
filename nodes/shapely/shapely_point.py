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

class SvExShapelyPointNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Point
    Tooltip: 2D Point
    """
    bl_idname = "SvExShapelyPointNode"
    bl_label = "2D Point"
    bl_icon = 'DOT'
    sv_dependencies = {'shapely'}

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_s = self.inputs['Vertices'].sv_get()
        verts_s = ensure_nesting_level(verts_s, 3)

        polygons_out = []
        for verts in verts_s:
            if len(verts) == 1:
                polygon = shapely.Point(verts[0])
            else:
                polygon = shapely.MultiPoint(verts)
            polygons_out.append(polygon)

        self.outputs['Geometry'].sv_set(polygons_out)

def register():
    bpy.utils.register_class(SvExShapelyPointNode)


def unregister():
    bpy.utils.unregister_class(SvExShapelyPointNode)

