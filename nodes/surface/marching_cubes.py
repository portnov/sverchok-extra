
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
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
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

        def make_function(self, variables):
            def function(x, y, z):
                variables.update(dict(x=x, y=y, z=z))
                #self.debug("Vs: %s", variables)
                return safe_eval(self.formula, variables)
            return np.vectorize(function)

        def get_variables(self):
            variables = get_variables(self.formula)
            variables.difference_update({'x', 'y', 'z'})
            return list(sorted(list(variables)))

        def adjust_sockets(self):
            variables = self.get_variables()
            for key in self.inputs.keys():
                if key not in variables and key not in {'Bounds', 'Value', 'Samples'}:
                    self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                    self.inputs.remove(self.inputs[key])
            for v in variables:
                if v not in self.inputs:
                    self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                    self.inputs.new('SvStringsSocket', v)

        def update(self):
            '''
            update analyzes the state of the node and returns if the criteria to start processing
            are not met.
            '''

            if not self.formula:
                return

            self.adjust_sockets()

        def get_input(self):
            variables = self.get_variables()
            inputs = {}

            for var in variables:
                if var in self.inputs and self.inputs[var].is_linked:
                    inputs[var] = self.inputs[var].sv_get()
            return inputs

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Bounds'].sv_get()
            value_s = self.inputs['Value'].sv_get()
            samples_s = self.inputs['Samples'].sv_get()

            if isinstance(value_s[0], (list, tuple)):
                value_s = value_s[0]

            var_names = self.get_variables()
            inputs = self.get_input()
            input_values = [inputs.get(name, [[0]]) for name in var_names]
            parameters = match_long_repeat([vertices_s, value_s, samples_s] + input_values)

            verts_out = []
            faces_out = []
            for vertices, value, samples, *var_values_s in zip(*parameters):
                if isinstance(samples, (list, tuple)):
                    samples = samples[0]
                if isinstance(value, (list, tuple)):
                    value = value[0]

                b1, b2 = self.get_bounds(vertices)
                b1n, b2n = np.array(b1), np.array(b2)
                self.debug("Bounds: %s - %s", b1, b2)

                for var_values in var_values_s:
                    variables = dict(zip(var_names, var_values))
                    self.debug("Vars: %s", variables)
                    self.debug("Eval for value = %s", value)

                    x_range = np.linspace(b1[0], b2[0], num=samples)
                    y_range = np.linspace(b1[1], b2[1], num=samples)
                    z_range = np.linspace(b1[2], b2[2], num=samples)
                    grid = np.meshgrid(x_range, y_range, z_range, indexing='ij')
                    func_values = self.make_function(variables.copy())(*grid)

                    new_verts, new_faces = mcubes.marching_cubes(
                            func_values,
                            value)                         # Isosurface value

                    new_verts = (new_verts / samples) * (b2n - b1n) + b1n
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

