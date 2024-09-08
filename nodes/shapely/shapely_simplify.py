import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely
from sverchok_extra.utils.shapely import union_collection

class SvExShapelySimplifyNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Simplify
    Tooltip: 2D Simplify Geometry
    """
    bl_idname = 'SvExShapelySimplifyNode'
    bl_label = '2D Simplify Geometry'
    bl_icon = 'MOD_SMOOTH'
    sv_dependencies = {'shapely'}

    tolerance : FloatProperty(
            name = "Tolerance",
            default = 0.1,
            min = 0.0,
            update = updateNode)

    union_all : BoolProperty(
            name = "Union Polygons",
            default = False,
            update = updateNode)

    preserve_topology : BoolProperty(
            name = "Preserve Topology",
            default = True,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.inputs.new('SvStringsSocket', "Tolerance").prop_name = 'tolerance'
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'union_all')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'preserve_topology')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))
        tolerance_s = self.inputs['Tolerance'].sv_get()
        tolerance_s = ensure_nesting_level(tolerance_s, 2)

        geometry_out = []
        for params in zip_long_repeat(geometry_s, tolerance_s):
            new_geometry = []
            for geometry, tolerance in zip_long_repeat(*params):
                if self.union_all:
                    geometry = union_collection(geometry)
                g = shapely.simplify(geometry,
                                     tolerance = tolerance,
                                     preserve_topology = self.preserve_topology)
                new_geometry.append(g)
            if flat_output:
                geometry_out.extend(new_geometry)
            else:
                geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelySimplifyNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelySimplifyNode)

