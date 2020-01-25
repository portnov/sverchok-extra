
from sverchok.utils.logging import info, exception

try:
    import scipy
    from scipy.interpolate import Rbf
    scipy_available = True
except ImportError as e:
    info("SciPy is not available, normal interpolation mode will not be available")
    scipy_available = False

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import bvhtree

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.logging import info, exception
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

from sverchok_extra.data.field.vector import SvExBvhAttractorVectorField, SvExBvhRbfNormalVectorField
from sverchok_extra.utils import rbf_functions

class SvExMeshNormalFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Mesh Normal Field
    Tooltip: Generate vector field by mesh normal at the nearest point
    """
    bl_idname = 'SvExMeshNormalFieldNode'
    bl_label = 'Mesh Nearest Normal'
    bl_icon = 'OUTLINER_OB_EMPTY'

    interpolate : BoolProperty(
        name = "Interpolate",
        default = False,
        update = updateNode)

    function : EnumProperty(
            name = "Function",
            items = rbf_functions,
            default = 'multiquadric',
            update = updateNode)

    def draw_buttons(self, context, layout):
        if scipy_available:
            layout.prop(self, "interpolate", toggle=True)
            if self.interpolate:
                layout.prop(self, "function")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvExVectorFieldSocket', "Field").display_shape = 'CIRCLE_DOT'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        faces_s = self.inputs['Faces'].sv_get()

        fields_out = []
        for vertices, faces in zip_long_repeat(vertices_s, faces_s):
            if self.interpolate:
                bvh = bvhtree.BVHTree.FromPolygons(vertices, faces)

                bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
                normals = np.array([f.normal for f in bm.faces])
                centers = np.array([f.calc_center_median() for f in bm.faces])
                bm.free()

                xs_from = centers[:,0]
                ys_from = centers[:,1]
                zs_from = centers[:,2]

                rbf = Rbf(xs_from, ys_from, zs_from, normals,
                        function = self.function,
                        mode = 'N-D')

                field = SvExBvhRbfNormalVectorField(bvh, rbf)
            else:
                field = SvExBvhAttractorVectorField(verts=vertices, faces=faces, use_normal=True)
            fields_out.append(field)
        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvExMeshNormalFieldNode)

def unregister():
    bpy.utils.unregister_class(SvExMeshNormalFieldNode)

