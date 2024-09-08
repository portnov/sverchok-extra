import numpy as np
import bpy
from mathutils import Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely

def transform_by_matrix(matrix):
    m = np.array(matrix)[:2, :2]
    v = np.array(matrix.translation)[:2]
    return lambda pts: (m @ pts.T).T + v

class SvExShapelyTransformNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Transform
    Tooltip: 2D Transform
    """
    bl_idname = 'SvExShapelyTransformNode'
    bl_label = '2D Transform Geometry'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_TRANSFORM_SOLID'
    sv_dependencies = {'shapely'}

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.inputs.new('SvMatrixSocket', "Matrix")
        self.outputs.new('SvGeom2DSocket', "Geometry")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))
        matrix_s = self.inputs['Matrix'].sv_get()
        matrix_s = ensure_nesting_level(matrix_s, 2, data_types=(Matrix,))

        geometry_out = []
        for params in zip_long_repeat(geometry_s, matrix_s):
            new_geometry = []
            for geometry, matrix in zip_long_repeat(*params):
                g = shapely.transform(geometry, transform_by_matrix(matrix))
                new_geometry.append(g)
            if flat_output:
                geometry_out.extend(new_geometry)
            else:
                geometry_out.append(new_geometry)

        self.outputs['Geometry'].sv_set(geometry_out)

def register():
    bpy.utils.register_class(SvExShapelyTransformNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyTransformNode)

