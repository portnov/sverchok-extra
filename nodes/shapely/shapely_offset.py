import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely

class SvExShapelyOffsetNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Offset Curve
    Tooltip: 2D Offset Curve
    """
    bl_idname = 'SvExShapelyOffsetNode'
    bl_label = '2D Curve Offset'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OFFSET'
    sv_dependencies = {'shapely'}

    distance : FloatProperty(
            name = "Distance",
            default = 0.1,
            update = updateNode)

    quad_segs : IntProperty(
            name = "Quad Segs",
            default = 8,
            min = 1,
            update = updateNode)

    join_styles = [
            ('round', "Round", "Round", 0),
            ('mitre', "Mitre", "Mitre", 1),
            ('bevel', "Bevel", "Bevel", 2)
        ]

    join_style : EnumProperty(
            name = "Join style",
            items = join_styles,
            default = 'round',
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.inputs.new('SvStringsSocket', "Distance").prop_name = 'distance'
        self.inputs.new('SvStringsSocket', "QuadSegs").prop_name = 'quad_segs'
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'join_style')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))
        distance_s = self.inputs['Distance'].sv_get()
        distance_s = ensure_nesting_level(distance_s, 2)
        quad_segs_s = self.inputs['QuadSegs'].sv_get()
        quad_segs_s = ensure_nesting_level(quad_segs_s, 2)

        geometry_out = []
        for params in zip_long_repeat(geometry_s, distance_s, quad_segs_s):
            new_geometry = []
            for geometry, distance, quad_segs in zip_long_repeat(*params):
                g = shapely.offset_curve(geometry, distance,
                                        quad_segs = quad_segs,
                                        join_style = self.join_style)
                new_geometry.append(g)
            if flat_output:
                geometry_out.extend(new_geometry)
            else:
                geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelyOffsetNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyOffsetNode)


