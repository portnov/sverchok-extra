# BEGIN GPL LICENSE BLOCK #####
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
# END GPL LICENSE BLOCK #####

from collections import defaultdict

import bpy
from bpy.props import CollectionProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, zip_long_repeat
from sverchok.utils.logging import info, debug
from sverchok_extra.utils.modules.spreadsheet.ui import *

class SvSpreadsheetNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: spreadsheet data input
    Tooltip: Input data with spreadsheet-like interface
    """

    bl_idname = 'SvSpreadsheetNode'
    bl_label = "Spreadsheet"
    bl_icon = 'VIEW_ORTHO'

    spreadsheet : PointerProperty(type=SvSpreadsheetData)

    def adjust_outputs(self, context):

        if self.out_mode == 'ROW':
            names = [row.name for row in self.spreadsheet.data]
            types = ['SvStringsSocket' for row in self.spreadsheet.data]
        elif self.out_mode == 'COL':
            names = [col.name for col in self.spreadsheet.columns]
            types = [type_sockets[col.data_type] for col in self.spreadsheet.columns]
        else:
            names = []
            types = []

        links = {sock.name: [link.to_socket for link in sock.links] for sock in self.outputs}
        for key in self.outputs.keys():
            if key not in {'Data', 'Rows', 'Columns'}:
                self.outputs.remove(self.outputs[key])

        new_socks = []
        for key, sock_type in zip(names, types):
            sock = self.outputs.new(sock_type, key)
            new_socks.append(sock)

        for new_sock in new_socks:
            for to_sock in links.get(new_sock.name, []):
                try:
                    self.id_data.links.new(new_sock, to_sock)
                except:
                    pass

        self.outputs['Data'].hide_safe = self.out_mode != 'NONE'
        self.outputs['Rows'].hide_safe = self.out_mode != 'NONE'
        self.outputs['Columns'].hide_safe = self.out_mode != 'NONE'
        updateNode(self, context)

    out_modes = [
            ('NONE', "Dictionaries", "Do not display separate outputs", 0),
            ('ROW', "By Rows", "Display separate output for each row", 1),
            ('COL', "By Columns", "Display separate output for each column", 2)
        ]

    out_mode : EnumProperty(
            name = "Outputs",
            items = out_modes,
            default = 'NONE',
            update = adjust_outputs)

    def sv_init(self, context):
        self.width = 500
        self.inputs.new('SvDictionarySocket', "Input")
        self.outputs.new('SvDictionarySocket', "Data")
        self.outputs.new('SvDictionarySocket', "Rows")
        self.outputs.new('SvDictionarySocket', "Columns")

        column = self.add_column()
        column.name = "Value"

        row = self.add_row()
        row.name = "Item"

    def sv_update(self):
        self.spreadsheet.set_node(self)
        self.adjust_inputs()

    def draw_buttons(self, context, layout):
        row = self.spreadsheet.draw(layout)
        row.prop(self, 'out_mode')

    def draw_buttons_ext(self, context, layout):
        layout.template_list("UI_UL_SvColumnDescriptorsList", "columns", self.spreadsheet, "columns", self.spreadsheet, "selected")

        row = layout.row(align=True)
        add = row.operator(SvSpreadsheetAddColumn.bl_idname, text='', icon='ADD')
        add.nodename = self.name
        add.treename = self.id_data.name

    def adjust_inputs(self):
        variables = self.spreadsheet.get_variables()
        for key in self.inputs.keys():
            if (key not in variables) and key not in ['Input']:
                self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('SvStringsSocket', v)

        formula_cols = self.spreadsheet.get_formula_cols()
        self.inputs['Input'].hide_safe = len(formula_cols) == 0

    def on_update_value(self, context):
        self.adjust_inputs()
        updateNode(self, context)

    def on_update_row_name(self, context):
        self.adjust_inputs()
        self.adjust_outputs(context)
        updateNode(self, context)

    def on_update_column(self, context):
        self.adjust_inputs()
        self.adjust_outputs(context)
        updateNode(self, context)

    def check_row_uniq(self):
        row_names = [row.name for row in self.spreadsheet.data]
        existing = set()
        for name in row_names:
            if name in existing:
                raise Exception(f"Row name `{name}` is duplicated!")
            existing.add(name)

    def check_column_uniq(self):
        col_names = [col.name for col in self.spreadsheet.columns]
        existing = set()
        for name in col_names:
            if name in existing:
                raise Exception(f"Column name `{name}` is duplicated!")
            existing.add(name)
        
    def add_row(self):
        data_row = self.spreadsheet.data.add()
        for column in self.spreadsheet.columns:
            item = data_row.items.add()
            item.treename = self.id_data.name
            item.nodename = self.name
        self.adjust_outputs(None)
        return data_row

    def remove_row(self, idx):
        self.spreadsheet.data.remove(idx)
        self.adjust_outputs(None)

    def move_row(self, selected_index, shift, context):
        next_index = selected_index + shift
        if (0 <= selected_index < len(self.spreadsheet.data)) and (0 <= next_index < len(self.spreadsheet.data)):
            self.spreadsheet.data.move(selected_index, next_index)
            self.adjust_outputs(context)
            #updateNode(self, context)

    def add_column(self):
        column = self.spreadsheet.columns.add()
        for data_row in self.spreadsheet.data:
            item = data_row.items.add()
            item.treename = self.id_data.name
            item.nodename = self.name
        self.adjust_outputs(None)
        return column

    def remove_column(self, idx):
        self.spreadsheet.columns.remove(idx)
        for data_row in self.spreadsheet.data:
            data_row.items.remove(idx)
        self.adjust_outputs(None)

    def move_column(self, selected_index, shift, context):
        next_index = selected_index + shift
        if (0 <= selected_index < len(self.spreadsheet.columns)) and (0 <= next_index < len(self.spreadsheet.columns)):
            self.spreadsheet.columns.move(selected_index, next_index)
            for data_row in self.spreadsheet.data:
                data_row.items.move(selected_index, next_index)
            self.adjust_outputs(context)
            #updateNode(self, context)

    def get_input(self):
        variables = self.spreadsheet.get_variables()
        inputs = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                inputs[var] = self.inputs[var].sv_get()
        return inputs

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.check_row_uniq()
        self.check_column_uniq()
        #self.adjust_outputs(None)

        input_data_s = self.inputs['Input'].sv_get(default = [None])

        var_names = self.spreadsheet.get_variables()
        inputs = self.get_input()
        input_values = [inputs.get(name, [[0]]) for name in var_names]
        if var_names:
            parameters = match_long_repeat([input_data_s] + input_values)
        else:
            parameters = [input_data_s]

        data_out = []
        rows_out = []
        columns_out = []
        specific_outs = defaultdict(list)
        for input_data, *objects in zip(*parameters):
            if var_names:
                var_values_s = zip_long_repeat(*objects)
            else:
                var_values_s = [[]]
            for var_values in var_values_s:
                variables = dict(zip(var_names, var_values))
            
                data = self.spreadsheet.evaluate(input_data, variables)
                data_out.append(data)

                rows = list(data.values())
                rows_out.extend(rows)

                columns = defaultdict(dict)
                for row_key, row in data.items():
                    for col_key, item in row.items():
                        columns[col_key][row_key] = item
                columns = list(columns.values())
                columns_out.extend(columns)

                if self.out_mode == 'ROW':
                    for sp_row, row in zip(self.spreadsheet.data, data.values()):
                        values = list(row.values())
                        specific_outs[sp_row.name].append(values)
                elif self.out_mode == 'COL':
                    for sp_col, column in zip(self.spreadsheet.columns, columns):
                        values = list(column.values())
                        specific_outs[sp_col.name].append(values)

        self.outputs['Data'].sv_set(data_out)
        self.outputs['Rows'].sv_set(rows_out)
        self.outputs['Columns'].sv_set(columns_out)

        for key, values in specific_outs.items():
            self.outputs[key].sv_set(values)

classes = [
        SvColumnDescriptor, SvSpreadsheetValue,
        SvSpreadsheetRow, SvSpreadsheetData,
        UI_UL_SvColumnDescriptorsList,
        SvSpreadsheetAddColumn, SvSpreadsheetRemoveColumn, SvSpreadsheetMoveColumn,
        SvSpreadsheetAddRow, SvSpreadsheetRemoveRow, SvSpreadsheetMoveRow,
        SvSpreadsheetNode
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

