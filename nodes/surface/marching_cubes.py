
from sverchok.utils.logging import info, exception

try:
    import mcubes
    mcubes_available = True
except ImportError as e:
    info("mcubes package is not available, Marching Cubes node will not be available")
    mcubes_available = False

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList
from sverchok.utils.modules.eval_formula import get_variables, safe_eval

if mcubes_available:

    class SvExMarchingCubesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Marching Cubes
        Tooltip: Marching Cubes
        """
        bl_idname = 'SvExMarchingCubesNode'
        bl_label = 'Marching Cubes'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'

        iso_value : FloatProperty(
                name = "Value",
                default = 1.0,
                update = updateNode)

        sample_size : IntProperty(
                name = "Samples",
                default = 50,
                min = 4,
                update = updateNode)

        formula: StringProperty(
                name = "Formula",
                default = "x*x + y*y + z*z",
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Bounds")
            self.inputs.new('SvStringsSocket', "Value").prop_name = 'iso_value'
            self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Faces")

        def draw_buttons(self, context, layout):
            layout.prop(self, "formula", text="")
        
        def get_bounds(self, vertices):
            vs = np.array(vertices)
            min = vs.min(axis=0)
            max = vs.max(axis=0)
            return min.tolist(), max.tolist()

        def evaluate(self, x, y, z):
            variables = dict(x=x, y=y, z=z)
            return safe_eval(self.formula, variables)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Bounds'].sv_get()
            value_s = self.inputs['Value'].sv_get()
            samples_s = self.inputs['Samples'].sv_get()

            if isinstance(value_s[0], (list, tuple)):
                value_s = value_s[0]

            verts_out = []
            faces_out = []
            for vertices, value, samples in zip_long_repeat(vertices_s, value_s, samples_s):
                if isinstance(samples, (list, tuple)):
                    samples = samples[0]
                if isinstance(value, (list, tuple)):
                    value = value[0]

                b1, b2 = self.get_bounds(vertices)

                self.info("Eval for value = %s", value)
                # Extract the 16-isosurface
                new_verts, new_faces = mcubes.marching_cubes_func(
                        tuple(b1), tuple(b2),
                        samples, samples, samples,              # Number of samples in each dimension
                        self.evaluate,                          # Implicit function
                        value)                         # Isosurface value

                new_verts, new_faces = new_verts.tolist(), new_faces.tolist()
                verts_out.append(new_verts)
                faces_out.append(new_faces)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Faces'].sv_set(faces_out)

def register():
    if mcubes_available:
        bpy.utils.register_class(SvExMarchingCubesNode)

def unregister():
    if mcubes_available:
        bpy.utils.unregister_class(SvExMarchingCubesNode)

