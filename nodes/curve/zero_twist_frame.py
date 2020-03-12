import numpy as np

from mathutils import Matrix, Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList

class SvExCurveZeroTwistFrameNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Curve Zero-Twist Frame
        Tooltip: Calculate Zero-Twist Perpendicular frame for curve
        """
        bl_idname = 'SvExCurveZeroTwistFrameNode'
        bl_label = 'Curve Zero-Twist Frame'
        bl_icon = 'CURVE_NCURVE'

        def sv_init(self, context):
            self.inputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'
            self.inputs.new('SvStringsSocket', "T")
            self.outputs.new('SvStringsSocket', "CumulativeTorsion")
            self.outputs.new('SvMatrixSocket', 'Matrix')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['Curve'].sv_get()
            ts_s = self.inputs['T'].sv_get()

            torsion_out = []
            matrix_out = []
            for curve, ts in zip_long_repeat(curve_s, ts_s):
                ts = np.array(ts)

                vectors = curve.evaluate_array(ts)
                torsions = curve.torsion_array(ts)
                matrices_np, normals, binormals = curve.frame_array(ts)

                dvs = vectors[1:] - vectors[:-1]
                lengths = np.linalg.norm(dvs, axis=1)
                lengths = np.insert(lengths, 0, 0)
                summands = lengths * torsions
                integral = np.cumsum(np.insert(summands, 0, 0))

                new_matrices = []
                for matrix_np, point, angle in zip(matrices_np, vectors, integral):
                    frenet_matrix = Matrix(matrix_np.tolist()).to_4x4()
                    rotation_matrix = Matrix.Rotation(-angle, 4, 'Z')
                    matrix = frenet_matrix @ rotation_matrix
                    matrix.translation = Vector(point)
                    new_matrices.append(matrix)

                torsion_out.append(integral.tolist())
                matrix_out.append(new_matrices)

            self.outputs['CumulativeTorsion'].sv_set(torsion_out)
            self.outputs['Matrix'].sv_set(matrix_out)

def register():
    bpy.utils.register_class(SvExCurveZeroTwistFrameNode)

def unregister():
    bpy.utils.unregister_class(SvExCurveZeroTwistFrameNode)

