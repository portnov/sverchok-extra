
import bpy
from bpy.types import NodeTree, NodeSocket

from sverchok.core.sockets import SvStringsSocket, SvSocketCommon
from sverchok.core.socket_data import (
    SvGetSocketInfo, SvGetSocket, SvSetSocket,
    SvNoDataError, sentinel)

class SvExSurfaceSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvExSurfaceSocket"
    bl_label = "Surface Socket"

    def get_prop_data(self):
        return {}

    def draw_color(self, context, node):
        return (0.1, 0.1, 1.0, 1.0)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy=True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

class SvExScalarFieldSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvExScalarFieldSocket"
    bl_label = "Scalar Field Socket"

    def get_prop_data(self):
        return {}

    def draw_color(self, context, node):
        return (0.9, 0.4, 0.1, 1.0)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy=True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

class SvExVectorFieldSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvExVectorFieldSocket"
    bl_label = "Vector Field Socket"

    def get_prop_data(self):
        return {}

    def draw_color(self, context, node):
        return (0.1, 0.1, 0.9, 1.0)

    def sv_get(self, default=sentinel, deepcopy=True, implicit_conversions=None):
        if self.is_linked and not self.is_output:
            source_data = SvGetSocket(self, deepcopy=True if self.needs_data_conversion() else deepcopy)
            return self.convert_data(source_data, implicit_conversions)

        if self.prop_name:
            return [[getattr(self.node, self.prop_name)[:]]]
        elif default is sentinel:
            raise SvNoDataError(self)
        else:
            return default

classes = [
        SvExSurfaceSocket,
        SvExScalarFieldSocket,
        SvExVectorFieldSocket
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

