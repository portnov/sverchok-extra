import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely
from sverchok_extra.utils.shapely import boundary

class SvExShapelyBoundaryNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Boundary
    Tooltip: 2D Boundary
    """
    bl_idname = 'SvExShapelyBoundaryNode'
    bl_label = '2D Boundary'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOLID_BOOLEAN'
    sv_dependencies = {'shapely'}

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))

        geometry_out = []
        for params in geometry_s:
            new_geometry = []
            for geometry in params:
                g = boundary(geometry)
                new_geometry.append(g)
            if flat_output:
                geometry_out.extend(new_geometry)
            else:
                geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelyBoundaryNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyBoundaryNode)

