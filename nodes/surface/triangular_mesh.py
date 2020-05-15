
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty

from sverchok.core.update_system import process_from_node
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.field.scalar import SvScalarField

from sverchok_extra.dependencies import pygalmesh

if pygalmesh is not None:

    class SvDomain(pygalmesh.DomainBase):
        def __init__(self, field, radius, iso_value):
            super().__init__()
            self.field = field
            self.radius = radius
            self.iso_value = iso_value

        def eval(self, x):
            return self.field.evaluate(x[0], x[1], x[2]) - self.iso_value

        def get_bounding_sphere_squared_radius(self):
            return self.radius**2

    class SvExUpdateGalMeshNodeOp(bpy.types.Operator):
        bl_idname = "node.sv_gal_gen_mesh_update"
        bl_label = "Update node"
        bl_options = {'REGISTER', 'INTERNAL'}

        node_tree : StringProperty()
        node_name : StringProperty()

        def execute(self, context):
            node = bpy.data.node_groups[self.node_tree].nodes[self.node_name]
            node.active = True
            process_from_node(node)
            node.active = False
            return {'FINISHED'}

    class SvExGalGenerateMeshNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Generate Mesh
        Tooltip: Generate Mesh
        """
        bl_idname = 'SvExGalGenerateMeshNode'
        bl_label = 'Implicit Surface Mesh'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EX_MCUBES'

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

        draft_properties_mapping = dict(
                cell_size = 'cell_size_draft'
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
            self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
            self.inputs.new('SvStringsSocket', "Value").prop_name = 'iso_value'
            self.inputs.new('SvStringsSocket', "CellSize").prop_name = 'cell_size'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Faces")

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
            radius_s = self.inputs['Radius'].sv_get()
            value_s = self.inputs['Value'].sv_get()
            cell_size_s = self.inputs['CellSize'].sv_get()

            fields_s = ensure_nesting_level(fields_s, 2, data_types=(SvScalarField,))

            verts_out = []
            faces_out = []

            parameters = zip_long_repeat(fields_s, radius_s, value_s, cell_size_s)
            for fields, radiuses, values, cell_sizes in parameters:
                for field, radius, value, cell_size in zip_long_repeat(fields, radiuses, values, cell_sizes):
                    domain = SvDomain(field, radius, value)
                    mesh = pygalmesh.generate_surface_mesh(domain, angle_bound=0.01, distance_bound=0.01, radius_bound=0.1)
                    new_verts = mesh.points.tolist()
                    new_faces = mesh.cells[0].data.tolist()
                    verts_out.append(new_verts)
                    faces_out.append(new_faces)

            self['verts_out'] = verts_out
            self['faces_out'] = faces_out

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Faces'].sv_set(faces_out)

def register():
    if pygalmesh is not None:
        bpy.utils.register_class(SvExUpdateGalMeshNodeOp)
        bpy.utils.register_class(SvExGalGenerateMeshNode)

def unregister():
    if pygalmesh is not None:
        bpy.utils.unregister_class(SvExGalGenerateMeshNode)
        bpy.utils.unregister_class(SvExUpdateGalMeshNodeOp)

