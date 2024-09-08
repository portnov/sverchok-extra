import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import ensure_nesting_level, get_data_nesting_level, zip_long_repeat, updateNode
from sverchok_extra.dependencies import shapely

class SvExShapelyDistanceNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Distance
    Tooltip: 2D Geometry Distance
    """
    bl_idname = 'SvExShapelyDistanceNode'
    bl_label = '2D Geometry Distance'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DISTANCE_LINE_LINE'
    sv_dependencies = {'shapely'}

    metrics = [
            ('CARTESIAN', "Cartesian", "Cartesian", 0),
            ('HAUSDORFF', "Hausdorff", "Hausdorff", 1),
            ('FRECHET', "Frechet", "Frechet", 2)
        ]
    def update_sockets(self, context):
        self.inputs['Density'].hide_safe = self.metric == 'CARTESIAN' or not self.specify_density

    metric : EnumProperty(
            name = "Metric",
            items = metrics,
            default = 'CARTESIAN',
            update = update_sockets)

    specify_density : BoolProperty(
            name = "Specify Density",
            default = False,
            update = update_sockets)

    density : FloatProperty(
            name = "Density",
            min = 0.0, max = 1.0,
            default = 0.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry1")
        self.inputs.new('SvGeom2DSocket', "Geometry2")
        self.inputs.new('SvStringsSocket', "Density").prop_name = 'density'
        self.outputs.new('SvStringsSocket', "Distance")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'metric')
        if self.metric != 'CARTESIAN':
            layout.prop(self, 'specify_density')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry1_s = self.inputs['Geometry1'].sv_get()
        geometry2_s = self.inputs['Geometry2'].sv_get()
        input_level = get_data_nesting_level(geometry1_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry1_s = ensure_nesting_level(geometry1_s, 2, data_types=(shapely.Geometry,))
        geometry2_s = ensure_nesting_level(geometry2_s, 2, data_types=(shapely.Geometry,))
        if self.specify_density:
            density_s = self.inputs['Density'].sv_get()
            density_s = ensure_nesting_level(density_s, 2)
        else:
            density_s = [[None]]

        distance_out = []
        for params in zip_long_repeat(geometry1_s, geometry2_s, density_s):
            new_distances = []
            for geometry1, geometry2, density in zip_long_repeat(*params):
                if self.metric == 'CARTESIAN':
                    distance = shapely.distance(geometry1, geometry2)
                elif self.metric == 'HAUSDORFF':
                    distance = shapely.hausdorff_distance(geometry1, geometry2,
                                                          densify = density)
                else:
                    distance = shapely.frechet_distance(geometry1, geometry2,
                                                          densify = density)
                new_distances.append(distance)
            if flat_output:
                distance_out.extend(new_distances)
            else:
                distance_out.append(new_distances)

        self.outputs['Distance'].sv_set(distance_out)

def register():
    bpy.utils.register_class(SvExShapelyDistanceNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyDistanceNode)

