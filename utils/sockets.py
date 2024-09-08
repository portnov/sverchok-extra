
import bpy
from bpy.types import NodeTree, NodeSocket

from sverchok.data_structure import flatten_data, graft_data
from sverchok.core.sockets import InterfaceSocket, SocketDomain, SvSocketCommon

from sverchok_extra.dependencies import shapely

class SvGeom2DSocket(SocketDomain, NodeSocket, SvSocketCommon):
    """Socket type for Shapely 2D Geometry"""
    bl_idname = 'SvGeom2DSocket'
    bl_label = "2D Geometry Socket"

    color = (0.64, 0.8, 0.96, 1.0)

    def do_flatten(self, data):
        return flatten_data(data, 1, data_types=(shapely.Geometry,))

    def do_graft(self, data):
        return graft_data(data, item_level=0, data_types=(shapely.Geometry,))

def register():
    bpy.utils.register_class(SvGeom2DSocket)

def unregister():
    bpy.utils.unregister_class(SvGeom2DSocket)

