
from sverchok.utils.logging import info, exception

try:
    from skimage import measure
    skimage_available = True
except ImportError as e:
    info("SciKit-Image package is not available")
    skimage_available = False

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, match_long_repeat

if skimage_available:

    class SvExMarchingSquaresNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Marching Squares
        Tooltip: Marching Squares
        """
        bl_idname = 'SvExMarchingSquaresNode'
        bl_label = 'Marching Squares'
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

        z_value : FloatProperty(
                name = "Z",
                default = 0.0,
                update = updateNode)

        min_x : FloatProperty(
                name = "Min X",
                default = -1.0,
                update = updateNode)

        max_x : FloatProperty(
                name = "Max X",
                default = 1.0,
                update = updateNode)

        min_y : FloatProperty(
                name = "Min Y",
                default = -1.0,
                update = updateNode)

        max_y : FloatProperty(
                name = "Max Y",
                default = 1.0,
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvExScalarFieldSocket', "Field").display_shape = 'CIRCLE_DOT'
            self.inputs.new('SvStringsSocket', "Value").prop_name = 'iso_value'
            self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
            self.inputs.new('SvStringsSocket', "MinX").prop_name = 'min_x'
            self.inputs.new('SvStringsSocket', "MaxX").prop_name = 'max_x'
            self.inputs.new('SvStringsSocket', "MinY").prop_name = 'min_y'
            self.inputs.new('SvStringsSocket', "MaxY").prop_name = 'max_y'
            self.inputs.new('SvStringsSocket', "Z").prop_name = 'z_value'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvStringsSocket', "Faces")

        def make_contour(self, samples, min_x, x_size, min_y, y_size, z, contour):
            n = len(contour)
            verts = []
            vert_0_bound = None
            vert_n_bound = None
            for i, (x0, y0) in enumerate(contour):

                if x0 <= 0:
                    if i == 0:
                        vert_0_bound = 'A'
                    elif i == n-1:
                        vert_n_bound = 'A'
                elif y0 <= 0:
                    if i == 0:
                        vert_0_bound = 'D'
                    elif i == n-1:
                        vert_n_bound = 'D'
                elif x0 >= samples-1:
                    if i == 0:
                        vert_0_bound = 'C'
                    elif i == n-1:
                        vert_n_bound = 'C'
                elif y0 >= samples-1:
                    if i == 0:
                        vert_0_bound = 'B'
                    elif i == n-1:
                        vert_n_bound = 'B'

                x = min_x + x_size * x0
                y = min_y + y_size * y0
                vertex = (x, y, z)
                verts.append(vertex)

            make_face = vert_0_bound == vert_n_bound

            edges = [(i, i+1) for i in range(n-1)]
            if make_face:
                edges.append((n-1, 0))
            if make_face:
                face = list(range(n))
                faces = [face]
            else:
                faces = []
            return verts, edges, faces

        def make_contours(self, samples, min_x, x_size, min_y, y_size, z, contours):
            verts = []
            edges = []
            faces = []
            for contour in contours:
                new_verts, new_edges, new_faces = self.make_contour(samples, min_x, x_size, min_y, y_size, z, contour)
                verts.append(new_verts)
                edges.append(new_edges)
                faces.append(new_faces)
            return verts, edges, faces

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            fields_s = self.inputs['Field'].sv_get()
            min_x_s = self.inputs['MinX'].sv_get()
            max_x_s = self.inputs['MaxX'].sv_get()
            min_y_s = self.inputs['MinY'].sv_get()
            max_y_s = self.inputs['MaxY'].sv_get()
            value_s = self.inputs['Value'].sv_get()
            z_value_s = self.inputs['Z'].sv_get()
            samples_s = self.inputs['Samples'].sv_get()

            if isinstance(value_s[0], (list, tuple)):
                value_s = value_s[0]
            if isinstance(z_value_s[0], (list, tuple)):
                z_value_s = z_value_s[0]

            parameters = zip_long_repeat(fields_s, min_x_s, max_x_s, min_y_s, max_y_s, z_value_s, value_s, samples_s)

            verts_out = []
            edges_out = []
            faces_out = []
            for field, min_x, max_x, min_y, max_y, z_value, value, samples in parameters:
                if isinstance(samples, (list, tuple)):
                    samples = samples[0]
                if isinstance(value, (list, tuple)):
                    value = value[0]
                if isinstance(min_x, (list, tuple)):
                    min_x = min_x[0]
                if isinstance(max_x, (list, tuple)):
                    max_x = max_x[0]
                if isinstance(min_y, (list, tuple)):
                    min_y = min_y[0]
                if isinstance(max_y, (list, tuple)):
                    max_y = max_y[0]
                if isinstance(z_value, (list, tuple)):
                    z_value = z_value[0]

                x_range = np.linspace(min_x, max_x, num=samples)
                y_range = np.linspace(min_y, max_y, num=samples)
                z_range = np.array([z_value])
                grid = np.meshgrid(x_range, y_range, z_range, indexing='ij')
                field_values = field.evaluate_grid(*grid)
                field_values = field_values[:,:,0]

                contours = measure.find_contours(field_values, level=value)

                x_size = (max_x - min_x)/samples
                y_size = (max_y - min_y)/samples

                new_verts, new_edges, new_faces = self.make_contours(samples, min_x, x_size, min_y, y_size, z_value, contours)
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Faces'].sv_set(faces_out)

def register():
    if skimage_available:
        bpy.utils.register_class(SvExMarchingSquaresNode)

def unregister():
    if skimage_available:
        bpy.utils.unregister_class(SvExMarchingSquaresNode)

