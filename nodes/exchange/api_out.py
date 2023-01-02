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

class SvExApiOutNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: API Output Node
    Tooltip: API Output
    """
    bl_idname = 'SvExApiOutNode'
    bl_label = 'API Output'
    bl_icon = 'FILE_REFRESH'

    def sv_init(self, context):
        self.inputs.new('SvLoopControlSocket', 'API')
        self.inputs.new('SvDictionarySocket', 'Output')

    output_data : StringProperty(
            name = "Output",
            options = {'SKIP_SAVE'}
        )

    def process(self):
        print("Processing", self)
        if not self.inputs['API'].is_linked:
            return
        data = self.inputs['Output'].sv_get()
        print("Output", data)
        self.output_data = json.dumps(data)

def register():
    bpy.utils.register_class(SvExApiOutNode)

def unregister():
    bpy.utils.unregister_class(SvExApiOutNode)

