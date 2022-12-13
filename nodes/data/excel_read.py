import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.utils.dictionary import SvDict

from sverchok_extra.dependencies import pyexcel

class SvReadExcelOperator(bpy.types.Operator, SvGenericNodeLocator):
    bl_idname = "node.sv_read_excel"
    bl_label = "read excel file"
    bl_options = {'INTERNAL', 'REGISTER'}

    def execute(self, context):
        node = self.get_node(context)

        if not node: return {'CANCELLED'}

        if not any(socket.is_linked for socket in node.outputs):
            return {'CANCELLED'}
        if not node.inputs['FilePath'].is_linked:
            return {'CANCELLED'}

        node.read_file()
        updateNode(node, context)

        return {'FINISHED'}

# https://stackoverflow.com/a/28666223
def numberToBase(n, b):
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(int(n % b))
        n //= b
    return digits[::-1]

def get_excel_column_name(n):
    digits = numberToBase(n, 26)
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return "".join([letters[d] for d in digits])

def make_column_names(cols):
    return [get_excel_column_name(n) for n in cols]

class SvReadExcelNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Read Excel spreadsheet
    Tooltip: Load data from Excel or LibreOffice spreadsheet
    """
    bl_idname = 'SvReadExcelNode'
    bl_label = 'Read Excel'
    bl_icon = 'IMPORT'

    use_row_names : BoolProperty(
            name = "Row names in first column",
            description = "Use row names from first column",
            default = False,
            update = updateNode)

    use_column_names : BoolProperty(
            name = "Column names in first row",
            description = "Use column names from first row",
            default = False,
            update = updateNode)

    out_modes = [
            ('LIST', "Nested lists", "Output data as nested lists", 0),
            ('ROW', "Dictionary By Rows", "Output dictionary by row name", 1),
            ('COL', "Dictionary By Columns", "Output dictionary by column name", 2),
            ('NEST', "Nested Dictionaries", "Output dictionary by row and column name", 3)
        ]

    def update_sockets(self, context):
        self.outputs['Data'].hide_safe = self.out_mode != 'LIST' or self.load_all_sheets
        self.outputs['Rows'].hide_safe = self.out_mode not in ['ROW', 'NEST']
        self.outputs['Columns'].hide_safe = self.out_mode != 'COL'
        self.outputs['Sheets'].hide_safe = not self.load_all_sheets or self.out_mode != 'LIST'
        self.inputs['Sheet'].hide_safe = self.load_all_sheets
        updateNode(self, context)

    out_mode : EnumProperty(
            name = "Outputs",
            items = out_modes,
            default = 'LIST',
            update = update_sockets)

    load_all_sheets : BoolProperty(
            name = "All sheets",
            description = "Load all sheets from the file",
            default = False,
            update = update_sockets)

    sheet_name : StringProperty(
            name = "Sheet",
            description = "Name of sheet inside the file",
            default = "Sheet1",
            update = update_sockets)

    def draw_buttons(self, context, layout):
        self.wrapper_tracked_ui_draw_op(layout, SvReadExcelOperator.bl_idname, icon='FILE_REFRESH', text="UPDATE")
        layout.label(text='Outputs:')
        layout.prop(self, 'out_mode', text='')
        if self.out_mode in ['ROW', 'NEST']:
            layout.prop(self, 'use_row_names')
        if self.out_mode in ['COL', 'NEST']:
            layout.prop(self, 'use_column_names')
        layout.prop(self, 'load_all_sheets')

    def sv_init(self, context):
        self.inputs.new('SvFilePathSocket', "FilePath")
        self.inputs.new('SvStringsSocket', "Sheet").prop_name = 'sheet_name'
        self.outputs.new('SvDictionarySocket', "Rows")
        self.outputs.new('SvDictionarySocket', "Columns")
        self.outputs.new('SvDictionarySocket', "Sheets")
        self.outputs.new('SvStringsSocket', "Data")
        self.update_sockets(context)

    def convert_sheet(self, sheet):
        def mk_dict(items):
            d = SvDict(items)
            d.inputs = dict((key, {'type': 'SvStringsSocket', 'name': key, 'nest': None}) for key in d.keys())
            return d

        def nested_dict_from_row(names, values):
            d = SvDict(zip(names, values))
            d.inputs = dict((key, {'type': 'SvStringsSocket', 'name': key, 'nest': None}) for key in d.keys())
            return d

        def mk_nested_dict(sheet):
            d = SvDict((n, nested_dict_from_row(sheet.colnames, sheet.row[n])) for n in sheet.rownames)
            d.inputs = dict((key, {'type': 'SvDictionarySocket', 'name': key, 'nest': item.inputs}) for key, item in d.items())
            return d

        if self.out_mode == 'LIST':
            return list(sheet.rows())
        elif self.out_mode == 'ROW':
            if self.use_row_names:
                sheet.name_rows_by_column(0)
            else:
                sheet.rownames = [f"R{i}" for i in sheet.row_range()]
            return mk_dict([(n, sheet.row[n]) for n in sheet.rownames])
        elif self.out_mode == 'COL':
            if self.use_column_names:
                sheet.name_columns_by_row(0)
            else:
                sheet.colnames = make_column_names(sheet.column_range())
            return mk_dict([(n, sheet.column[n]) for n in sheet.colnames])
        elif self.out_mode == 'NEST':
            if self.use_row_names:
                sheet.name_rows_by_column(0)
            else:
                sheet.rownames = [f"R{i}" for i in sheet.row_range()]
            if self.use_column_names:
                sheet.name_columns_by_row(0)
            else:
                sheet.colnames = make_column_names(sheet.column_range())
            return mk_nested_dict(sheet)

    def read_file(self):
        path = self.inputs['FilePath'].sv_get()[0][0]
        sheet_name = self.inputs['Sheet'].sv_get()[0][0]

        book = pyexcel.get_book(file_name = path)
        if not sheet_name:
            book_data = dict((sheet_name, self.convert_sheet(book[sheet_name])) for sheet_name in book.sheet_names())
            book_data = SvDict(book_data)
            nested_socket_type = 'SvStringsSocket' if self.out_mode == 'LIST' else 'SvDictionarySocket' 
            get_nested_inputs = lambda sheet_data: None if self.out_mode == 'LIST' else sheet_data.inputs
            book_data.inputs = dict((sheet_name, {'type': nested_socket_type, 'name': sheet_name, 'nest': get_nested_inputs(sheet_data)}) for sheet_name, sheet_data in book_data.items())
            book_data = book_data
            if self.out_mode == 'LIST':
                self.outputs['Sheets'].sv_set([book_data])
            elif self.out_mode in ['ROW', 'NEST']:
                self.outputs['Rows'].sv_set([book_data])
            else:
                self.outputs['Columns'].sv_set([book_data])
        else:
            sheet_data = self.convert_sheet(book[sheet_name])
            if self.out_mode == 'LIST':
                self.outputs['Data'].sv_set([sheet_data])
            elif self.out_mode in ['ROW', 'NEST']:
                self.outputs['Rows'].sv_set([sheet_data])
            else:
                self.outputs['Columns'].sv_set([sheet_data])

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        if not self.inputs['FilePath'].is_linked:
            return

        self.read_file()

def register():
    print("REGISTER EXCEL")
    bpy.utils.register_class(SvReadExcelOperator)
    bpy.utils.register_class(SvReadExcelNode)

def unregister():
    bpy.utils.unregister_class(SvReadExcelNode)
    bpy.utils.unregister_class(SvReadExcelOperator)

