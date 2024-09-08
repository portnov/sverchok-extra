
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely

class SvExShapelyBooleanNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Boolean
    Tooltip: 2D Boolean
    """
    bl_idname = 'SvExShapelyBooleanNode'
    bl_label = '2D Boolean'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOLID_BOOLEAN'
    sv_dependencies = {'shapely'}

    operations = [
            ('UNION', "Union", "Union", 0),
            ('INTERSECTION', "Intersection", "Intersection", 1),
            ('DIFFERENCE', "Difference", "Difference", 2),
            ('SYMMDIFF', "Symmetric Difference", "Symmetric Difference", 3)
        ]

    operation : EnumProperty(
            name = "Operation",
            items = operations,
            default = 'UNION',
            update = updateNode)

    def update_sockets(self, context):
        self.inputs['Geometry1'].hide_safe = self.accumulate_nested
        self.inputs['Geometry2'].hide_safe = self.accumulate_nested
        self.inputs['Geometries'].hide_safe = not self.accumulate_nested

    accumulate_nested : BoolProperty(
            name = "Accumulate Nested",
            default = False,
            update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry1")
        self.inputs.new('SvGeom2DSocket', "Geometry2")
        self.inputs.new('SvGeom2DSocket', "Geometries")
        self.outputs.new('SvGeom2DSocket', "Geometry")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation')
        layout.prop(self, 'accumulate_nested')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_out = []
        if not self.accumulate_nested:
            geometry1_s = self.inputs['Geometry1'].sv_get()
            geometry2_s = self.inputs['Geometry2'].sv_get()
            input_level = get_data_nesting_level(geometry1_s, data_types=(shapely.Geometry,))
            flat_output = input_level == 1
            geometry1_s = ensure_nesting_level(geometry1_s, 2, data_types=(shapely.Geometry,))
            geometry2_s = ensure_nesting_level(geometry2_s, 2, data_types=(shapely.Geometry,))
            for params in zip_long_repeat(geometry1_s, geometry2_s):
                new_geometry = []
                for geometry1, geometry2 in zip_long_repeat(*params):
                    if self.operation == 'UNION':
                        geometry = geometry1.union(geometry2)
                    elif self.operation == 'INTERSECTION':
                        geometry = geometry1.intersection(geometry2)
                    elif self.operation == 'DIFFERENCE':
                        geometry = geometry1.difference(geometry2)
                    else:
                        geometry = geometry1.symmetric_difference(geometry2)
                    new_geometry.append(geometry)
                if flat_output:
                    geometry_out.extend(new_geometry)
                else:
                    geometry_out.append(new_geometry)
        else:
            geometries_s = self.inputs['Geometries'].sv_get()
            input_level = get_data_nesting_level(geometries_s, data_types=(shapely.Geometry,))
            flat_output = input_level == 1
            geometries_s = ensure_nesting_level(geometries_s, 3, data_types=(shapely.Geometry,))
            for params in geometries_s:
                new_geometry = []
                for geometries in params:
                    if self.operation == 'UNION':
                        geometry = shapely.union_all(geometries)
                    elif self.operation == 'INTERSECTION':
                        geometry = shapely.intersection_all(geometries)
                    elif self.operation == 'DIFFERENCE':
                        geometry = geometries[0]
                        for g in geometries[1:]:
                            geometry = geometry.difference(g)
                    else:
                        geometry = shapely.symmetric_difference_all(geometries)
                    new_geometry.append(geometry)

                if flat_output:
                    geometry_out.extend(new_geometry)
                else:
                    geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelyBooleanNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyBooleanNode)

