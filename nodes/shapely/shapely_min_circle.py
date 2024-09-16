import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.geom import circle_approximation_2d
from sverchok_extra.dependencies import shapely

class SvExShapelyMinBoundingCircleNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Bounding Circle
    Tooltip: Calculate Minimum bounding circle of 2D object
    """
    bl_idname = 'SvExShapelyMinBoundingCircleNode'
    bl_label = '2D Bounding Circle'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOLID_BOOLEAN'
    sv_dependencies = {'shapely'}

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.outputs.new('SvGeom2DSocket', "Geometry")
        self.outputs.new('SvVerticesSocket', "Center")
        self.outputs.new('SvStringsSocket', "Radius")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))

        geometry_out = []
        center_out = []
        radius_out = []
        for params in geometry_s:
            new_geometry = []
            new_center = []
            new_radius = []
            for geometry in params:
                g = shapely.minimum_bounding_circle(geometry)
                coords = shapely.get_coordinates(g)
                circle = circle_approximation_2d(coords)
                center = tuple(circle.center) + (0.0, )
                new_geometry.append(g)
                new_center.append(center)
                new_radius.append(circle.radius)
            if flat_output:
                geometry_out.extend(new_geometry)
                center_out.extend(new_center)
                radius_out.extend(new_radius)
            else:
                center_out.append(new_center)
                radius_out.append(new_radius)
                geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)
        self.outputs['Center'].sv_set(center_out)
        self.outputs['Radius'].sv_set(radius_out)

def register():
    bpy.utils.register_class(SvExShapelyMinBoundingCircleNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyMinBoundingCircleNode)

