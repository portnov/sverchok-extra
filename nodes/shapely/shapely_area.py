
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely

class SvExShapelyAreaNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Polygon Area
    Tooltip: 2D Polygon Area
    """
    bl_idname = 'SvExShapelyAreaNode'
    bl_label = '2D Polygon Area'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_AREA'
    sv_dependencies = {'shapely'}

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.outputs.new('SvStringsSocket', "Area")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))

        area_out = []
        for params in geometry_s:
            new_area = []
            for geometry in params:
                area = geometry.area
                new_area.append(area)
            if flat_output:
                area_out.extend(new_area)
            else:
                area_out.append(new_area)

        self.outputs['Area'].sv_set(area_out)

def register():
    bpy.utils.register_class(SvExShapelyAreaNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyAreaNode)

