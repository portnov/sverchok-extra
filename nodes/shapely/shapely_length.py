import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely

class SvExShapelyLengthNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Length
    Tooltip: 2D Geometry Length
    """
    bl_idname = 'SvExShapelyLengthNode'
    bl_label = '2D Geometry Length'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_PATH_LENGTH'
    sv_dependencies = {'shapely'}

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.outputs.new('SvStringsSocket', "Length")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))

        length_out = []
        for params in geometry_s:
            new_length = []
            for geometry in params:
                length = shapely.length(geometry)
                new_length.append(length)
            if flat_output:
                length_out.extend(new_length)
            else:
                length_out.append(new_length)

        self.outputs['Length'].sv_set(length_out)

def register():
    bpy.utils.register_class(SvExShapelyLengthNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyLengthNode)

