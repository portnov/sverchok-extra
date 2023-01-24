# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
try:
    import awkward as ak
except ImportError:
    ak = None

import bpy
from bpy.props import EnumProperty

from sverchok.node_tree import SverchCustomTreeNode


class SvArrMathNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrMathNode'
    bl_label = 'Math (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    functions = [
        ("", "Function", "", 0),
        ("ADD", "Add", "", 1),
        ("SUBTRACT", "Subtract", "", 2),
        ("MULTIPLY", "Multiply", "", 3),
        ("DIVIDE", "Divide", "", 4),
        ("", "Trigonometry", "", 5),
        ("SIN", "Sine", "", 6),
        ("COS", "Cosine", "", 7),
    ]

    func_code = {
        'ADD': lambda x, y: x+y,
        'SUBTRACT': lambda x, y: x-y,
        'MULTIPLY': lambda x, y: x*y,
        'DIVIDE': lambda x, y: x/y,
        'SIN': lambda x, y: np.sin(x),
        'COS': lambda x, y: np.cos(x),
    }

    def update_function(self, context):
        num = 1 if self.function in {'SIN', 'COS'} else 2
        self.inputs[1].enabled = num > 1
        self.process_node(context)

    function: EnumProperty(items=functions,
                           default='ADD',
                           update=update_function)

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, "function", text="")

    def sv_init(self, context):
        s = self.inputs.new('SvStringsSocket', "Data")
        s.use_prop = True
        s.show_property_type = True
        s = self.inputs.new('SvStringsSocket', "Data")
        s.use_prop = True
        s.show_property_type = True

        self.outputs.new('SvStringsSocket', "Data")

    def process(self):
        x = self.inputs[0].sv_get(deepcopy=False)
        x = x if self.inputs[0].is_linked else x[0][0]
        y = self.inputs[1].sv_get(deepcopy=False)
        y = y if self.inputs[1].is_linked else y[0][0]
        self.outputs[0].sv_set(self.func_code[self.function](x, y))


register, unregister = bpy.utils.register_classes_factory([SvArrMathNode])
