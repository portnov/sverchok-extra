# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from itertools import cycle

from sverchok.utils.handle_blender_data import correct_collection_length

try:
    import awkward as ak
except ImportError:
    ak = None

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.generating_objects import SvViewerLightNode, SvMeshData


class SvArrMeshViewerNode(
    SvViewerLightNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrMeshViewerNode'
    bl_label = 'Mesh Viewer (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    mesh_data: bpy.props.CollectionProperty(type=SvMeshData, options={'SKIP_SAVE'})
    fast_mesh_update: bpy.props.BoolProperty(
        default=True,
        update=lambda s, c: s.process_node(c),
        description="Usually should be enabled. If some glitches with"
                    " mesh update, switch it off")

    def sv_draw_buttons(self, context, layout):
        self.draw_viewer_properties(layout)

    def draw_buttons_fly(self, layout):
        super().draw_buttons_fly(layout)
        col = layout.column()
        col.prop(self, 'fast_mesh_update')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Array')
        self.init_viewer()

    def sv_copy(self, other):
        super().sv_copy(other)
        self.mesh_data.clear()

    def sv_free(self):
        for data in self.mesh_data:
            data.remove_data()
        super().sv_free()

    def bake(self):
        for obj_d, me_d in zip(self.object_data, self.mesh_data):
            obj = obj_d.copy()
            me = me_d.copy()
            obj.data = me

    def process(self):
        mesh = self.inputs[0].sv_get(deepcopy=False, default=None)
        if not self.is_active or mesh is None:
            return

        # regenerate mesh data blocks
        if mesh.verts.ndim == 2:
            verts = mesh.verts.to_numpy()
            edges = mesh.edges.to_list() if 'edges' in mesh.fields else []
            faces = mesh.faces.to_list() if 'faces' in mesh.fields else []
            correct_collection_length(self.mesh_data, 1)
            self.mesh_data[0].regenerate_mesh(
                self.base_data_name,
                verts,
                edges,
                faces,
                make_changes_test=self.fast_mesh_update)
        elif mesh.verts.ndim == 3:
            verts = mesh.verts
            edges = mesh.edges.to_list() if 'edges' in mesh.fields else [[]]
            faces = mesh.faces.to_list() if 'faces' in mesh.fields else [[]]
            obj_num = len(mesh)
            correct_collection_length(self.mesh_data, obj_num)
            create_mesh_data = zip(self.mesh_data, cycle(verts), cycle(edges), cycle(faces))
            for me_data, v, e, f in create_mesh_data:
                me_data.regenerate_mesh(
                    self.base_data_name, v.to_numpy(), e, f, make_changes_test=self.fast_mesh_update)
        else:
            raise ValueError(f"Vertices dimensions should 2 or 3, {mesh.verts.ndim} is given")

        # regenerate object data blocks
        # tree.sv_show triggers scene update so the tree attribute also should
        # be taken into account
        self.regenerate_objects([self.base_data_name],
                                [d.mesh for d in self.mesh_data],
                                to_show=[self.id_data.sv_show and self.show_objects])
        objs = [obj_data.obj for obj_data in self.object_data]
        self.outputs[0].sv_set(objs)


register, unregister = bpy.utils.register_classes_factory([SvArrMeshViewerNode])
