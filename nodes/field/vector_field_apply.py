
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.logging import info, exception

class SvExVectorFieldApplyNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Vector Field Apply
    Tooltip: Apply Vector Field to vertices
    """
    bl_idname = 'SvExVectorFieldApplyNode'
    bl_label = 'Apply Vector Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    coefficient : FloatProperty(
            name = "Coefficient",
            default = 1.0,
            update = updateNode)

    iterations : IntProperty(
            name = "Iterations",
            default = 1,
            min = 1,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvExVectorFieldSocket', "Field").display_shape = 'CIRCLE_DOT'
        d = self.inputs.new('SvVerticesSocket', "Vertices")
        d.use_prop = True
        d.prop = (0.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Coefficient").prop_name = 'coefficient'
        self.inputs.new('SvStringsSocket', "Iterations").prop_name = 'iterations'
        self.outputs.new('SvVerticesSocket', 'Vertices')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        coeffs_s = self.inputs['Coefficient'].sv_get()
        fields_s = self.inputs['Field'].sv_get()
        iterations_s = self.inputs['Iterations'].sv_get()

        verts_out = []
        for field, vertices, coeffs, iterations in zip_long_repeat(fields_s, vertices_s, coeffs_s, iterations_s):
            if isinstance(iterations, (list, tuple)):
                iterations = iterations[0]

            if len(vertices) == 0:
                new_verts = []
            elif len(vertices) == 1:
                vertex = vertices[0]
                for i in range(iterations):
                    vector = field.evaluate(*vertex)
                    coeff = coeffs[0]
                    vertex = (coeff * np.array(vertex) + vector).tolist()
                new_verts = [vertex]
            else:
                fullList(coeffs, len(vertices))
                for i in range(iterations):
                    XYZ = np.array(vertices)
                    xs = XYZ[:,0][np.newaxis][np.newaxis]
                    ys = XYZ[:,1][np.newaxis][np.newaxis]
                    zs = XYZ[:,2][np.newaxis][np.newaxis]
                    new_xs, new_ys, new_zs = field.evaluate_grid(xs, ys, zs)
                    new_vectors = np.dstack((new_xs[0,0,:], new_ys[0,0,:], new_zs[0,0,:]))
                    new_vectors = np.array(coeffs)[np.newaxis].T * new_vectors[0]
                    vertices = XYZ + new_vectors
                new_verts = vertices.tolist()

            verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvExVectorFieldApplyNode)

def unregister():
    bpy.utils.unregister_class(SvExVectorFieldApplyNode)

