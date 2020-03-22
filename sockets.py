
import bpy
from bpy.types import NodeTree, NodeSocket
from mathutils import Matrix

from sverchok.core.sockets import SvStringsSocket, SvSocketCommon
from sverchok.core.socket_data import (
    SvGetSocketInfo, SvGetSocket, SvSetSocket,
    SvNoDataError, sentinel)
from sverchok.core.socket_conversions import DefaultImplicitConversionPolicy
from sverchok.data_structure import get_other_socket, get_data_nesting_level
from sverchok.utils.logging import debug, info

from .data.field.scalar import SvExConstantScalarField
from .data.field.vector import SvExMatrixVectorField, SvExConstantVectorField

def is_matrix_to_vfield(socket):
    other = get_other_socket(socket)
    return other.bl_idname == 'SvMatrixSocket' and socket.bl_idname == 'SvExVectorFieldSocket'

def is_vertex_to_vfield(socket):
    other = get_other_socket(socket)
    return other.bl_idname == 'SvVerticesSocket' and socket.bl_idname == 'SvExVectorFieldSocket'

def is_string_to_sfield(socket):
    other = get_other_socket(socket)
    return other.bl_idname == 'SvStringsSocket' and socket.bl_idname == 'SvExScalarFieldSocket'

def matrices_to_vfield(data):
    if isinstance(data, Matrix):
        return SvExMatrixVectorField(data)
    elif isinstance(data, (list, tuple)):
        return [matrices_to_vfield(item) for item in data]
    else:
        raise TypeError("Unexpected data type from Matrix socket: %s" % type(data))

def vertices_to_vfield(data):
    if isinstance(data, (tuple, list)) and len(data) == 3 and isinstance(data[0], (float, int)):
        return SvExConstantVectorField(data)
    elif isinstance(data, (list, tuple)):
        return [vertices_to_vfield(item) for item in data]
    else:
        raise TypeError("Unexpected data type from Vertex socket: %s" % type(data))

def numbers_to_sfield(data):
    if isinstance(data, (int, float)):
        return SvExConstantScalarField(data)
    elif isinstance(data, (list, tuple)):
        return [numbers_to_sfield(item) for item in data]
    else:
        raise TypeError("Unexpected data type from String socket: %s" % type(data))

class SvExImplicitConversionPolicy(DefaultImplicitConversionPolicy):
    @classmethod
    def convert(cls, socket, source_data):
        if is_matrix_to_vfield(socket):
            return matrices_to_vfield(source_data) 
        elif is_vertex_to_vfield(socket):
            return vertices_to_vfield(source_data)
        elif is_string_to_sfield(socket):
            level = get_data_nesting_level(source_data)
            if level > 2:
                raise TypeError("Too high data nesting level for Number -> Scalar Field conversion: %s" % level)
            return numbers_to_sfield(source_data)
        else:
            super().convert(socket, source_data)

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

class SvExCurveSocket(NodeSocket, SvSocketCommon):
    bl_idname = "SvExCurveSocket"
    bl_label = "Curve Socket"

    def get_prop_data(self):
        return {}

    def draw_color(self, context, node):
        return (0.5, 0.6, 1.0, 1.0)

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
        if implicit_conversions is None:
            implicit_conversions = SvExImplicitConversionPolicy
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
        if implicit_conversions is None:
            implicit_conversions = SvExImplicitConversionPolicy
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
        SvExCurveSocket,
        SvExSurfaceSocket,
        SvExScalarFieldSocket,
        SvExVectorFieldSocket
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

