import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely

class SvExShapelyConcaveHullNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Concave Hull
    Tooltip: 2D Concave Hull
    """
    bl_idname = 'SvExShapelyConcaveHullNode'
    bl_label = '2D Concave Hull'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CONCAVE_HULL'
    sv_dependencies = {'shapely'}

    ratio : FloatProperty(
            name = "Ratio",
            default = 0.0,
            min = 0.0, max = 1.0,
            update = updateNode)

    allow_holes : BoolProperty(
            name = "Allow Holes",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.inputs.new('SvStringsSocket', "Ratio").prop_name = 'ratio'
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'allow_holes')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))
        ratio_s = self.inputs['Ratio'].sv_get()
        ratio_s = ensure_nesting_level(ratio_s, 2)

        geometry_out = []
        for params in zip_long_repeat(geometry_s, ratio_s):
            new_geometry = []
            for geometry, ratio in zip_long_repeat(*params):
                g = shapely.concave_hull(geometry,
                                         ratio = ratio,
                                         allow_holes = self.allow_holes)
                new_geometry.append(g)
            if flat_output:
                geometry_out.extend(new_geometry)
            else:
                geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelyConcaveHullNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyConcaveHullNode)

