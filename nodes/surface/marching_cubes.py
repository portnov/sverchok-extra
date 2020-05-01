
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat
from sverchok.utils.logging import info, exception

from sverchok_extra.dependencies import mcubes, skimage
from sverchok_extra.utils.marching_cubes import isosurface_np

if skimage is not None:
    import skimage.measure

if mcubes is not None or skimage is not None:

    class SvExMarchingCubesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Marching Cubes
        Tooltip: Marching Cubes
        """
        bl_idname = 'SvExMarchingCubesNode'
        bl_label = 'Marching Cubes'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EX_MCUBES'

        iso_value : FloatProperty(
                name = "Value",
                default = 1.0,
                update = updateNode)

        sample_size : IntProperty(
                name = "Samples",
                default = 50,
                min = 4,
                update = updateNode)

        sample_size_draft : IntProperty(
                name = "[D] Samples",
                default = 25,
                min = 4,
                update = updateNode)

        draft_properties_mapping = dict(
                sample_size = 'sample_size_draft'
            )

        def get_modes(self, context):
            modes = []
            if skimage is not None:
                modes.append(("skimage", "SciKit-Image", "SciKit-Image", 0))
            if mcubes is not None:
                modes.append(("mcubes", "PyMCubes", "PyMCubes", 1))
            modes.append(('python', "Pure Python", "Pure Python implementation", 2))
            return modes

        @throttled
        def update_sockets(self, context):
            self.outputs['VertexNormals'].hide_safe = self.implementation != 'skimage'

        implementation : EnumProperty(
                name = "Implementation",
                items = get_modes,
                update = update_sockets)

        def sv_init(self, context):
            self.inputs.new('SvScalarFieldSocket', "Field")
            self.inputs.new('SvVerticesSocket', "Bounds")
            self.inputs.new('SvStringsSocket', "Value").prop_name = 'iso_value'
            self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Faces")
            self.outputs.new('SvVerticesSocket', "VertexNormals")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.prop(self, "implementation", text="")
        
        def draw_label(self):
            label = self.label or self.name
            if self.id_data.sv_draft:
                label = "[D] " + label
            return label

        def get_bounds(self, vertices):
            vs = np.array(vertices)
            min = vs.min(axis=0)
            max = vs.max(axis=0)
            return min.tolist(), max.tolist()

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            fields_s = self.inputs['Field'].sv_get()
            vertices_s = self.inputs['Bounds'].sv_get()
            value_s = self.inputs['Value'].sv_get()
            samples_s = self.inputs['Samples'].sv_get()

            if isinstance(value_s[0], (list, tuple)):
                value_s = value_s[0]

            parameters = match_long_repeat([fields_s, vertices_s, value_s, samples_s])

            verts_out = []
            faces_out = []
            normals_out = []
            for field, vertices, value, samples in zip(*parameters):
                if isinstance(samples, (list, tuple)):
                    samples = samples[0]
                if isinstance(value, (list, tuple)):
                    value = value[0]

                b1, b2 = self.get_bounds(vertices)
                b1n, b2n = np.array(b1), np.array(b2)
                self.debug("Bounds: %s - %s", b1, b2)

                self.debug("Eval for value = %s", value)

                x_range = np.linspace(b1[0], b2[0], num=samples)
                y_range = np.linspace(b1[1], b2[1], num=samples)
                z_range = np.linspace(b1[2], b2[2], num=samples)
                xs, ys, zs = np.meshgrid(x_range, y_range, z_range, indexing='ij')
                func_values = field.evaluate_grid(xs.flatten(), ys.flatten(), zs.flatten())
                func_values = func_values.reshape((samples, samples, samples))

                if self.implementation == 'mcubes':
                    new_verts, new_faces = mcubes.marching_cubes(
                            func_values,
                            value)                         # Isosurface value

                    new_verts = (new_verts / samples) * (b2n - b1n) + b1n
                    new_verts, new_faces = new_verts.tolist(), new_faces.tolist()
                    new_normals = []
                elif self.implementation == 'skimage':
                    spacing = tuple(1 / (b2n - b1n))
                    new_verts, new_faces, normals, values = skimage.measure.marching_cubes_lewiner(
                            func_values, level = value,
                            #spacing = spacing,
                            step_size = 1)
                    new_verts = (new_verts / samples) * (b2n - b1n) + b1n
                    new_verts, new_faces = new_verts.tolist(), new_faces.tolist()
                    new_normals = normals.tolist()
                else: # python
                    new_verts, new_faces = isosurface_np(func_values, value)
                    new_verts = (new_verts / samples) * (b2n - b1n) + b1n
                    new_verts = new_verts.tolist()
                    new_normals = []

                verts_out.append(new_verts)
                faces_out.append(new_faces)
                normals_out.append(new_normals)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Faces'].sv_set(faces_out)
            self.outputs['VertexNormals'].sv_set(normals_out)

        def does_support_draft_mode(self):
            return True

def register():
    if mcubes is not None or skimage is not None:
        bpy.utils.register_class(SvExMarchingCubesNode)

def unregister():
    if mcubes is not None or skimage is not None:
        bpy.utils.unregister_class(SvExMarchingCubesNode)

