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
from bpy.props import IntProperty, EnumProperty, BoolProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.dictionary import SvDict

class SvExApiInNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: API Input Node
    Tooltip: API Input
    """
    bl_idname = 'SvExApiInNode'
    bl_label = 'API Input'
    bl_icon = 'FILE_REFRESH'

    def update_input(self, context):
        print("I", self.input_data)
        updateNode(self, context)

    input_data : StringProperty(
            name = "Input",
            default = '',
            options = {'SKIP_SAVE'},
            update = update_input
        )

    def sv_init(self, context):
        self.outputs.new('SvLoopControlSocket', 'API')
        self.outputs.new('SvDictionarySocket', 'Input')

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

def register():
    bpy.utils.register_class(SvExApiInNode)

def unregister():
    bpy.utils.unregister_class(SvExApiInNode)

