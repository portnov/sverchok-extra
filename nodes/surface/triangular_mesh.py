
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.field.scalar import SvScalarField

from sverchok_extra.dependencies import pygalmesh, scipy

if pygalmesh is not None and scipy is not None:

    from scipy.interpolate import RegularGridInterpolator

    class SvDomain(pygalmesh.DomainBase):
        def __init__(self, field, b1, b2, samples, iso_value):
            super().__init__()
            self.field = field
            self.iso_value = iso_value
            self.b1 = b1
            self.b2 = b2
            x_range, y_range, z_range, self.volume = build_volume(b1, b2, samples, field, iso_value)
            self.interpolator = RegularGridInterpolator((x_range, y_range, z_range), self.volume)

        def eval(self, x):
            if (x < self.b1).any() or (x > self.b2).any():
                return 0
            return self.interpolator(x)

        def get_bounding_sphere_squared_radius(self):
            dx = self.b2[0] - self.b1[0]
            dy = self.b2[1] - self.b1[1]
            dz = self.b2[2] - self.b1[2]
            return (dx**2 + dy**2 + dz**2)/4.0

def build_volume(b1, b2, samples, field, iso_value):
    x_range = np.linspace(b1[0], b2[0], num=samples)
    y_range = np.linspace(b1[1], b2[1], num=samples)
    z_range = np.linspace(b1[2], b2[2], num=samples)
    xs, ys, zs = np.meshgrid(x_range, y_range, z_range, indexing='ij')
    func_values = field.evaluate_grid(xs.flatten(), ys.flatten(), zs.flatten())
    m = func_values.min()
    M = func_values.max()
    print(f"Values: {m} - {M}")
    func_values = func_values - iso_value
    #func_values[func_values > iso_value] = 0
    func_values = func_values.reshape((samples, samples, samples))
    return x_range, y_range, z_range, func_values

class SvExUpdateGalMeshNodeOp(bpy.types.Operator):
    bl_idname = "node.sv_gal_gen_mesh_update"
    bl_label = "Update node"
    bl_options = {'REGISTER', 'INTERNAL'}

    node_tree : StringProperty()
    node_name : StringProperty()

    def execute(self, context):
        node = bpy.data.node_groups[self.node_tree].nodes[self.node_name]
        node.active = True
        node.process_node(None)
        node.active = False
        return {'FINISHED'}

class SvExGalGenerateMeshNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Generate Mesh
    Tooltip: Generate Mesh
    """
    bl_idname = 'SvExGalGenerateMeshNode'
    bl_label = 'Implicit Surface Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_MCUBES'
    sv_dependencies = {'pygalmesh', 'scipy'}

    iso_value : FloatProperty(
            name = "Value",
            default = 1.0,
            update = updateNode)

    radius : FloatProperty(
            name = "Bounding Radius",
            default = 1.0,
            update = updateNode)

    cell_size : FloatProperty(
            name = "Cell Size",
            default = 0.1,
            min = 0,
            update = updateNode)

    cell_size_draft : FloatProperty(
            name = "[D] Cell Size",
            default = 0.1,
            min = 0,
            update = updateNode)

    active : BoolProperty(
            name = "LIVE",
            default = True,
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
            cell_size = 'cell_size_draft',
            sample_size = 'sample_size_draft'
        )

    def does_support_draft_mode(self):
        return True

    def draw_buttons(self, context, layout):
        layout.prop(self, "active", toggle=True)
        if not self.active:
            op = layout.operator(SvExUpdateGalMeshNodeOp.bl_idname, text = "Update")
            op.node_tree = self.id_data.name
            op.node_name = self.name

    def draw_label(self):
        label = self.label or self.name
        if self.id_data.sv_draft:
            label = "[D] " + label
        return label

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        self.inputs.new('SvVerticesSocket', "Bounds")
        self.inputs.new('SvStringsSocket', "Value").prop_name = 'iso_value'
        self.inputs.new('SvStringsSocket', "SampleSize").prop_name = 'sample_size'
        self.inputs.new('SvStringsSocket', "CellSize").prop_name = 'cell_size'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Faces")

    def get_bounds(self, vertices):
        vs = np.array(vertices)
        min = vs.min(axis=0)
        max = vs.max(axis=0)
        return min.tolist(), max.tolist()

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        if not self.active:
            verts_out = self.get('verts_out', [])
            faces_out = self.get('faces_out', [])
            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Faces'].sv_set(faces_out)
            return

        fields_s = self.inputs['Field'].sv_get()
        bounds_s = self.inputs['Bounds'].sv_get()
        value_s = self.inputs['Value'].sv_get()
        cell_size_s = self.inputs['CellSize'].sv_get()
        sample_size_s = self.inputs['SampleSize'].sv_get()

        fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))
        bounds_s = ensure_nesting_level(bounds_s, 4)

        verts_out = []
        faces_out = []

        parameters = zip_long_repeat(fields_s, bounds_s, value_s, sample_size_s, cell_size_s)
        for fields, bounds_i, values, sample_sizes, cell_sizes in parameters:
            for field, bounds, value, sample_size, cell_size in zip_long_repeat(fields, bounds_i, values, sample_sizes, cell_sizes):
                b1, b2 = self.get_bounds(bounds)
                b1n, b2n = np.array(b1), np.array(b2)
                domain = SvDomain(field, b1n, b2n, sample_size, value)
                mesh = pygalmesh.generate_surface_mesh(domain, angle_bound=30, distance_bound=0.5, radius_bound=0.5)
                new_verts = mesh.points.tolist()
                new_faces = mesh.cells[0].data.tolist()
                verts_out.append(new_verts)
                faces_out.append(new_faces)

        self['verts_out'] = verts_out
        self['faces_out'] = faces_out

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Faces'].sv_set(faces_out)


def register():
    bpy.utils.register_class(SvExUpdateGalMeshNodeOp)
    bpy.utils.register_class(SvExGalGenerateMeshNode)


def unregister():
    bpy.utils.unregister_class(SvExGalGenerateMeshNode)
    bpy.utils.unregister_class(SvExUpdateGalMeshNodeOp)
