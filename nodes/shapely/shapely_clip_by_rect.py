import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely

class SvExShapelyClipByRectNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Clip Rectangle
    Tooltip: Clip 2D geometry by a rectangle
    """
    bl_idname = 'SvExShapelyClipByRectNode'
    bl_label = '2D Clip by Rectangle'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOLID_BOOLEAN'
    sv_dependencies = {'shapely'}

    x_min : FloatProperty(
            name = "Min X",
            default = -1.0,
            update = updateNode)

    x_max : FloatProperty(
            name = "Max X",
            default = 1.0,
            update = updateNode)

    y_min : FloatProperty(
            name = "Min Y",
            default = -1.0,
            update = updateNode)

    y_max : FloatProperty(
            name = "Max Y",
            default = 1.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.inputs.new('SvStringsSocket', "XMin").prop_name = 'x_min'
        self.inputs.new('SvStringsSocket', "XMax").prop_name = 'x_max'
        self.inputs.new('SvStringsSocket', "YMin").prop_name = 'y_min'
        self.inputs.new('SvStringsSocket', "YMax").prop_name = 'y_max'
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))

        x_min_s = self.inputs['XMin'].sv_get()
        x_min_s = ensure_nesting_level(x_min_s, 2)
        x_max_s = self.inputs['XMax'].sv_get()
        x_max_s = ensure_nesting_level(x_max_s, 2)
        y_min_s = self.inputs['YMin'].sv_get()
        y_min_s = ensure_nesting_level(y_min_s, 2)
        y_max_s = self.inputs['YMax'].sv_get()
        y_max_s = ensure_nesting_level(y_max_s, 2)

        geometry_out = []
        for params in zip_long_repeat(geometry_s, x_min_s, x_max_s, y_min_s, y_max_s):
            new_geometry = []
            for geometry, x_min, x_max, y_min, y_max in zip_long_repeat(*params):
                g = shapely.clip_by_rect(geometry, x_min, y_min, x_max, y_max)
                new_geometry.append(g)
            if flat_output:
                geometry_out.extend(new_geometry)
            else:
                geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelyClipByRectNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyClipByRectNode)

