# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import numpy as np

import bpy
from bpy.props import EnumProperty

from sverchok_extra.utils.array_math import scale_vert
from sverchok.node_tree import SverchCustomTreeNode

try:
    import awkward as ak
except ImportError:
    ak = None


class SvArrVectorMathNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrVectorMathNode'
    bl_label = 'Vector Math (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    functions = [
        ("ADD", "Add", "", 0),
        ("SUBTRACT", "Subtract", "", 1),
        ("MULTIPLY", "Multiply", "", 2),
        ("DIVIDE", "Divide", "", 3),
        ("", "", "", 4),
        ("LEN", "Length", "", 5),
        ("", "", "", 6),
        ("NORMALIZE", "Normalize", "", 7),
        ("SCALE", "Scale", "", 8),
    ]

    func_code = {
        'ADD': lambda x, y: x + y,
        'SUBTRACT': lambda x, y: x - y,
        'MULTIPLY': lambda x, y: x * y,
        'DIVIDE': lambda x, y: x / y,
        'LEN': lambda x, y: ak.sum(x**2, axis=-1)**0.5,
        'NORMALIZE': lambda x, y: x / (ak.sum(x**2, axis=-1)**0.5)[..., np.newaxis],
        'SCALE': scale_vert,
    }

    def update_function(self, context):
        num = 1 if self.function in {'LEN'} else 2
        self.inputs[1].enabled = num > 1

        show_value = self.function in {'SCALE'}
        self.inputs[1].enabled = not show_value
        self.inputs[2].enabled = show_value

        out_t = 'SvStringsSocket' if self.function in {'LEN'} else 'SvVerticesSocket'
        if self.outputs[0].bl_idname != out_t:
            self.outputs[0].replace_socket(out_t)
        self.process_node(context)

    function: EnumProperty(items=functions,
                           default='ADD',
                           update=update_function)

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, "function", text="")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vector').use_prop = True
        self.inputs.new('SvVerticesSocket', 'Vector').use_prop = True
        s = self.inputs.new('SvStringsSocket', 'Value')
        s.use_prop = True
        s.enabled = False
        self.outputs.new('SvVerticesSocket', 'Data')

    def process(self):
        x = self.inputs[0].sv_get(deepcopy=False)
        x = x if self.inputs[0].is_linked else ak.Array(x[0][0])
        y = self.inputs[1].sv_get(deepcopy=False)
        y = y if self.inputs[1].is_linked else ak.Array(y[0][0])
        z = self.inputs[2].sv_get(deepcopy=False)
        z = z if self.inputs[2].is_linked else ak.Array(z[0])
        y = z if self.function in {'SCALE'} else y
        self.outputs[0].sv_set(self.func_code[self.function](x, y))


register, unregister = bpy.utils.register_classes_factory([SvArrVectorMathNode])
