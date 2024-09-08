import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely

def make_points(pts):
    return shapely.MultiPoint(pts)

class SvExShapelyVoronoiNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Voronoi
    Tooltip: 2D Voronoi
    """
    bl_idname = 'SvExShapelyVoronoiNode'
    bl_label = '2D Voronoi'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'
    sv_dependencies = {'shapely'}

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Sites")
        self.inputs.new('SvGeom2DSocket', "ExtendTo")
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sites_s = self.inputs['Sites'].sv_get()
        input_level = get_data_nesting_level(sites_s)
        flat_output = input_level == 3
        sites_s = ensure_nesting_level(sites_s, 4)
        if self.inputs['ExtendTo'].is_linked:
            geometry_s = self.inputs['ExtendTo'].sv_get()
            geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))
        else:
            geometry_s = [[None]]

        geometry_out = []
        for params in zip_long_repeat(sites_s, geometry_s):
            new_geometry = []
            for sites, geometry in zip_long_repeat(*params):
                v = shapely.voronoi_polygons(make_points(sites),
                                            extend_to = geometry)
                new_geometry.append(list(v.geoms))
            if flat_output:
                geometry_out.extend(new_geometry)
            else:
                geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelyVoronoiNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyVoronoiNode)

