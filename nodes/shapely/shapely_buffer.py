import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely

class SvExShapelyBufferNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Dilate / Erode
    Tooltip: 2D Dilate / Erode
    """
    bl_idname = 'SvExShapelyBufferNode'
    bl_label = '2D Dilate or Erode'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOLID_BOOLEAN'
    sv_dependencies = {'shapely'}

    distance : FloatProperty(
            name = "Distance",
            default = 0.1,
            update = updateNode)

    operations = [
            ('DILATE', "Dilate", "Dilate", 0),
            ('ERODE', "Erode", "Erode", 1)
        ]

    operation : EnumProperty(
            name = "Operation",
            items = operations,
            default = 'DILATE',
            update = updateNode)

    cap_styles = [
            ('round', "Round", "Round", 0),
            ('square', "Square", "Square", 1),
            ('flat', "Flat", "Flat", 2)
        ]

    cap_style : EnumProperty(
            name = "Cap style",
            items = cap_styles,
            default = 'round',
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

    quad_segs : IntProperty(
            name = "Quad Segs",
            default = 16,
            min = 1,
            update = updateNode)

    single_sided : BoolProperty(
            name = "Single Sided",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.inputs.new('SvStringsSocket', "Distance").prop_name = 'distance'
        self.inputs.new('SvStringsSocket', "QuadSegs").prop_name = 'quad_segs'
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation', expand=True)
        layout.prop(self, 'single_sided')
        layout.prop(self, 'cap_style')
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
                if self.operation == 'ERODE':
                    distance = -distance
                g = shapely.buffer(geometry, distance,
                                    quad_segs = quad_segs,
                                    cap_style = self.cap_style,
                                    join_style = self.join_style,
                                    single_sided = self.single_sided)
                new_geometry.append(g)
            if flat_output:
                geometry_out.extend(new_geometry)
            else:
                geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelyBufferNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyBufferNode)

