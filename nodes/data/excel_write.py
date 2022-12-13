import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, ensure_nesting_level, transpose_list
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.utils.dictionary import SvDict

from sverchok_extra.dependencies import pyexcel

class SvWriteExcelOperator(bpy.types.Operator, SvGenericNodeLocator):
    bl_idname = "node.sv_write_excel"
    bl_label = "write excel file"
    bl_options = {'INTERNAL', 'REGISTER'}

    def execute(self, context):
        node = self.get_node(context)

        if not node: return {'CANCELLED'}

        node.write_file()
        updateNode(node,context)
        return {'FINISHED'}

class SvWriteExcelNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Write Excel spreadsheet
    Tooltip: Save data to Excel or LibreOffice spreadsheet
    """
    bl_idname = 'SvWriteExcelNode'
    bl_label = 'Write Excel'
    bl_icon = 'EXPORT'
    sv_dependencies = {'pyexcel'}

    in_modes = [
            ('LIST', "Nested lists", "Input data as nested lists", 0),
            ('ROW', "Dictionary By Rows", "Input dictionary by row name", 1),
            ('COL', "Dictionary By Columns", "Input dictionary by column name", 2),
            ('NEST', "Nested Dictionaries", "Input dictionary by row and column name", 3)
        ]

    def update_sockets(self, context):
        self.inputs['Sheet'].hide_safe = self.per_sheet
        self.inputs['Data'].hide_safe = not (self.in_mode == 'LIST' and not self.per_sheet)
        self.inputs['Sheets'].hide_safe = not (self.in_mode == 'LIST' and self.per_sheet)
        self.inputs['Rows'].hide_safe = self.in_mode not in ['ROW', 'NEST']
        self.inputs['Columns'].hide_safe = self.in_mode != 'COL'
        updateNode(self, context)

    in_mode : EnumProperty(
            name = "Input",
            items = in_modes,
            default = 'LIST',
            update = update_sockets)

    per_sheet : BoolProperty(
            name = "Per-sheet data",
            description = "Write all sheets to the file at once",
            default = False,
            update = update_sockets)

    sheet_name : StringProperty(
            name = "Sheet",
            description = "Name of sheet inside the file",
            default = "Sheet1",
            update = update_sockets)

    auto_write : BoolProperty(
            name = "Auto Write",
            description = "Write to file on each node tree processing",
            default = False,
            update = updateNode)

    write_row_names : BoolProperty(
            name = "Row names",
            description = "Write row names",
            default = False,
            update = updateNode)

    write_column_names : BoolProperty(
            name = "Column names",
            description = "Write column names",
            default = False,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Data")
        self.inputs.new('SvDictionarySocket', "Rows")
        self.inputs.new('SvDictionarySocket', "Columns")
        self.inputs.new('SvDictionarySocket', "Sheets")
        self.inputs.new('SvFilePathSocket', "FilePath")
        self.inputs.new('SvStringsSocket', "Sheet").prop_name = 'sheet_name'
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'auto_write')
        self.wrapper_tracked_ui_draw_op(layout, SvWriteExcelOperator.bl_idname, icon='FILE_REFRESH', text="UPDATE")
        layout.label(text = 'Input:')
        layout.prop(self, 'in_mode', text='')
        layout.prop(self, 'per_sheet')
        if self.in_mode in ['ROW', 'NEST']:
            layout.prop(self, 'write_row_names')
        if self.in_mode in ['COL', 'NEST']:
            layout.prop(self, 'write_column_names')

    def convert_by_rows(self, data):
        if self.write_row_names:
            data = [[key] + ensure_nesting_level(row, 1) for key, row in data.items()]
        else:
            data = [ensure_nesting_level(row, 1) for row in data.values()]
        return data

    def convert_by_columns(self, data):
        column_names = list(data.keys())
        columns = [ensure_nesting_level(column, 1) for column in data.values()]
        data = transpose_list(columns)
        if self.write_column_names:
            data = [column_names] + data
        return data
    
    def convert_nested(self, data):
        row_names = list(data.keys())
        n_rows = len(row_names)
        column_names = [set(row.keys()) for row in data.values()]
        column_names = set.union(*column_names)
        column_names = list(sorted(column_names))
        n_columns = len(column_names)
        result = [[None for c in column_names] for r in row_names]
        for i, row in enumerate(data.values()):
            for column_name, value in row.items():
                j = column_names.index(column_name)
                result[i][j] = value
        if self.write_column_names:
            result = [column_names] + result
        if self.write_row_names:
            if self.write_column_names:
                row_names = ["\\"] + row_names
            result = [[row_name] + row for row_name, row in zip(row_names, result)]
        return result

    def write_file(self):
        path = self.inputs['FilePath'].sv_get()[0][0]
        sheet_name = self.inputs['Sheet'].sv_get()[0][0]

        if self.in_mode == 'LIST':
            if self.per_sheet:
                book_data = self.inputs['Sheets'].sv_get()[0]
            else:
                data = self.inputs['Data'].sv_get()
                data = ensure_nesting_level(data, 2)
                book_data = {sheet_name : data}
        elif self.in_mode == 'ROW':
            data = self.inputs['Rows'].sv_get()
            if self.per_sheet:
                book_data = {key: self.convert_by_rows(sheet) for key, sheet in data.items()}
            else:
                book_data = {sheet_name : self.convert_by_rows(data)}
        elif self.in_mode == 'COL':
            data = self.inputs['Columns'].sv_get()
            if self.per_sheet:
                book_data = {key: self.convert_by_columns(sheet) for key, sheet in data.items()}
            else:
                book_data = {sheet_name : self.convert_by_columns(data)}
        elif self.in_mode == 'NEST':
            data = self.inputs['Rows'].sv_get()
            if self.per_sheet:
                book_data = {key: self.convert_nested(sheet) for key, sheet in data.items()}
            else:
                book_data = {sheet_name : self.convert_nested(data)}

        print("B", book_data)
        book = pyexcel.get_book(bookdict = book_data)
        book.save_as(path)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        if not self.inputs['FilePath'].is_linked:
            return

        if self.auto_write:
            self.write_file()

def register():
    bpy.utils.register_class(SvWriteExcelOperator)
    bpy.utils.register_class(SvWriteExcelNode)

def unregister():
    bpy.utils.unregister_class(SvWriteExcelNode)
    bpy.utils.unregister_class(SvWriteExcelOperator)

