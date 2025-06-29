import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok_extra.utils.svg_import import parse_svg
from sverchok_extra.dependencies import svgelements

class SvReadSvgOperator(bpy.types.Operator, SvGenericNodeLocator):
    bl_idname = "node.sv_read_svg"
    bl_label = "read SVG file"
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

class SvReadSvgNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Read SVG curves
    Tooltip: Load curves from SVG file
    """
    bl_idname = 'SvReadSvgNode'
    bl_label = 'Read SVG'
    bl_icon = 'IMPORT'
    sv_dependencies = {'svgelements'}

    svg_ppi : FloatProperty(
            name = "PPI",
            description = "SVG document resolution",
            default = 96.0,
            update = updateNode)

    concat_paths : BoolProperty(
            name = "Concatenate paths",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        self.wrapper_tracked_ui_draw_op(layout, SvReadSvgOperator.bl_idname, icon='FILE_REFRESH', text="UPDATE")
        layout.prop(self, 'concat_paths')
        layout.prop(self, 'svg_ppi')

    def sv_init(self, context):
        self.inputs.new('SvFilePathSocket', "FilePath")
        self.outputs.new('SvCurveSocket', "Curves")

    def read_file(self):
        path = self.inputs['FilePath'].sv_get()[0][0]
        curves = parse_svg(path, ppi=self.svg_ppi, concatenate_paths=self.concat_paths)
        self.outputs['Curves'].sv_set(curves)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        if not self.inputs['FilePath'].is_linked:
            return

        self.read_file()

def register():
    bpy.utils.register_class(SvReadSvgOperator)
    bpy.utils.register_class(SvReadSvgNode)

def unregister():
    bpy.utils.unregister_class(SvReadSvgNode)
    bpy.utils.unregister_class(SvReadSvgOperator)

