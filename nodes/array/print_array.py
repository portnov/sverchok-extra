# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

try:
    import awkward as ak
except ImportError:
    ak = None

import bpy
from bpy.props import EnumProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import bgl_callback_nodeview as sv_bgl


class SvPrintArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvPrintArrayNode'
    bl_label = 'Inspect Array'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    modes = [
        ('PRINT', 'Print', '', 0),
        ('TYPE', 'Type', '', 1),
        ('DIMENSIONS', 'Dimensions', '', 2),
        ('FIELDS', 'Fields', '', 3),
        ('LAYOUT', 'Layout', '', 4),
    ]

    mode: EnumProperty(items=modes, update=lambda s, c: s.process_node(c))
    field: StringProperty(update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'mode', text='')
        col = layout.column()
        if not self.get('valid', True):
            col.alert = True
        col.prop(self, 'field')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')

    def sv_free(self):
        sv_bgl.callback_disable(self.node_id)

    def process(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=None)
        if data is None:
            sv_bgl.callback_disable(self.node_id)
            return
        if not hasattr(data, '__len__'):  # probably a number
            sv_bgl.draw_text(self, str(data))
            return
        field = self.field if self.field in data.fields else None
        self['valid'] = not (field is None and self.field)
        if field:
            data = data[field]
        if self.mode == 'PRINT':
            # text = repr(data)
            text = data.show(type=True, stream=None)
        elif self.mode == 'TYPE':
            text = data.typestr
        elif self.mode == 'DIMENSIONS':
            text = str(data.ndim)
        elif self.mode == 'FIELDS':
            text = str(data.fields)
        elif self.mode == 'LAYOUT':
            text = str(data.layout)
        else:
            raise TypeError(f"Unknown {self.mode=}")
        sv_bgl.draw_text(self, text)


register, unregister = bpy.utils.register_classes_factory([SvPrintArrayNode])
