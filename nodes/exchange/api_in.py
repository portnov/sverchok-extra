# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import json

import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import IntProperty, EnumProperty, BoolProperty, StringProperty, PointerProperty, CollectionProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.dictionary import SvDict
from sverchok.utils.logging import info, debug

SUPPORTED_TYPES = [
        ('SvStringsSocket', "Numbers", "Socket type for numbers or arbitrary data", 0),
        ('SvVerticesSocket', "Vectors", "Socket type for vectors or points", 1)
    ]

class SvApiInputDescriptor(PropertyGroup):
    def update_type(self, context):
        if hasattr(context, 'node'):
            context.node.on_update_descriptor(context)
        else:
            info("update_type: no node in context")

    name : StringProperty(name="Name", update=update_type)
    socket_type : EnumProperty(name = "Type",
                    items = SUPPORTED_TYPES,
                    default = SUPPORTED_TYPES[0][0],
                    update = update_type
                )

class SvApiInputAdd(bpy.types.Operator):
    bl_label = "Add API input socket"
    bl_idname = "sverchok.api_input_add"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        node.add_input()
        updateNode(node, context)
        return {'FINISHED'}

class SvApiInputMove(bpy.types.Operator):
    bl_label = "Move API input socket"
    bl_idname = "sverchok.api_input_shift"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')
    shift : IntProperty(name='shift')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        selected_index = self.item_index
        node.move_input(self.item_index, self.shift, context)
        return {'FINISHED'}

class SvApiInputRemove(bpy.types.Operator):
    bl_label = "Remove API input socket"
    bl_idname = "sverchok.api_input_remove"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        idx = self.item_index
        node.remove_input(idx)
        updateNode(node, context)
        return {'FINISHED'}

class UI_UL_SvApiInputsList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        row = layout.row(align=True)
        row.prop(item, 'name', text='')
        row.prop(item, 'socket_type', text='')

        up = row.operator(SvApiInputMove.bl_idname, text='', icon='TRIA_UP')
        up.nodename = data.nodename
        up.treename = data.treename
        up.item_index = index
        up.shift = -1

        down = row.operator(SvApiInputMove.bl_idname, text='', icon='TRIA_DOWN')
        down.nodename = data.nodename
        down.treename = data.treename
        down.item_index = index
        down.shift = 1

        remove = row.operator(SvSpreadsheetRemoveColumn.bl_idname, text='', icon='REMOVE')
        remove.nodename = data.nodename
        remove.treename = data.treename
        remove.item_index = index

class SvExApiInNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: API Input Node
    Tooltip: API Input
    """
    bl_idname = 'SvExApiInNode'
    bl_label = 'API Input'
    bl_icon = 'FILE_REFRESH'

    def update_input(self, context):
        #print("I", self.input_data)
        updateNode(self, context)

    input_data : StringProperty(
            name = "Input",
            default = '',
            options = {'SKIP_SAVE'},
            update = update_input
        )

    api_inputs : CollectionProperty(name = "Inputs", type = SvApiInputDescriptor)
    new_input_name : StringProperty(name = "New input name", options = {'SKIP_SAVE'})

    def sv_init(self, context):
        self.outputs.new('SvLoopControlSocket', 'API')
        self.add_input()

    def sv_update(self, context):
        for sock in self.inputs:
            if sock.bl_idname == 'SvChameleonSocket' and sock.links:
                sock.catch_props()

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'new_input_name')
        add = row.operator(SvApiInputAdd.bl_idname, text='', icon='ADD')
        add.nodename = self.name
        add.treename = self.id_data.name

    def custom_draw_socket(self, socket, context, layout):
        row = layout.row(align=True)

    def add_input(self):
        print("ADD INPUT")
        item = self.api_inputs.add()
        item.name = self.new_input_name
        item.socket_type = 'SvChameleonSocket'
        socket = self.outputs.new('SvChameleonSocket', self.new_input_name)
        socket.custom_draw = 

    def remove_input(self, input_idx):
        print("REMOVE INPUT", input_idx)

    def move_input(self, input_idx, shift, context):
        print("MOVE INPUT:", input_idx, shift)

    def process(self):
        if not self.outputs['API'].is_linked:
            return
        if not self.input_data:
            return

        data = self.input_data
        data = json.loads(self.input_data)
        if isinstance(data, dict):
            data = SvDict.from_dict(data)
        elif isinstance(data, list):
            data = [SvDict.from_dict(item) for item in data]
        else:
            raise Exception(f"Unexpected input data type: {type(data)}: {data}")

        self.outputs['Input'].sv_set([data])

classes = [
    SvApiInputDescriptor, 
    SvApiInputAdd, SvApiInputMove, SvApiInputRemove,
    UI_UL_SvApiInputsList,
    SvExApiInNode ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

