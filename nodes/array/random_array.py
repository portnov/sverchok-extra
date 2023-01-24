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
from bpy.props import EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode


class SvRandomArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvRandomArrayNode'
    bl_label = 'Random array'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    type_modes = [
        ("FLOAT", "Float", "", 0),
        ("INT", "Integer", "", 1),
        ("VECTOR", "Vector", "", 2),
    ]

    def mode_change(self, context):
        mode = self.type_mode
        sock_type = mode.lower() if mode in {'FLOAT', 'INT'} else 'float'
        self.inputs['Min'].default_property_type = sock_type
        self.inputs['Max'].default_property_type = sock_type

        self.inputs['Min'].enabled = mode in {'FLOAT', 'INT'}
        self.inputs['Max'].enabled = mode in {'FLOAT', 'INT'}
        self.inputs['Vector Min'].enabled = mode == 'VECTOR'
        self.inputs['Vector Max'].enabled = mode == 'VECTOR'
        out_type = 'SvVerticesSocket' if mode == 'VECTOR' else 'SvStringsSocket'
        if self.outputs[0].bl_idname != out_type:
            self.outputs[0].replace_socket(out_type)
        self.process_node(context)

    type_mode: EnumProperty(
        name='Number Type',
        items=type_modes,
        update=mode_change)
    seed: IntProperty(update=lambda s, c: s.process_node(c))

    def sv_init(self, context):
        s = self.inputs.new('SvStringsSocket', "Size")
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 1
        self.inputs.new('SvStringsSocket', "Min").use_prop = True
        s = self.inputs.new('SvStringsSocket', "Max")
        s.use_prop = True
        s.default_float_property = 1
        s.default_int_property = 1
        s = self.inputs.new('SvVerticesSocket', "Vector Min")
        s.use_prop = True
        s.enabled = False
        s = self.inputs.new('SvVerticesSocket', "Vector Max")
        s.use_prop = True
        s.default_property = 1, 1, 1
        s.enabled = False

        self.outputs.new('SvStringsSocket', "Data")

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, "type_mode", text="")
        layout.prop(self, "seed")

    def process(self):
        sizes = self.inputs['Size'].sv_get(deepcopy=False)
        sizes = sizes if self.inputs['Size'].is_linked else sizes[0][0]
        min_val = self.inputs['Min'].sv_get(deepcopy=False)
        if not self.inputs['Min'].is_linked:
            min_val = min_val[0][0]
        max_val = self.inputs['Max'].sv_get(deepcopy=False)
        if not self.inputs['Max'].is_linked:
            max_val = max_val[0][0]
        min_vec = self.inputs['Vector Min'].sv_get(deepcopy=False)
        if not self.inputs['Vector Min'].is_linked:
            min_vec = ak.Array(min_vec[0][0])
        max_vec = self.inputs['Vector Max'].sv_get(deepcopy=False)
        if not self.inputs['Vector Max'].is_linked:
            max_vec = ak.Array(max_vec[0][0])

        rng = np.random.default_rng(self.seed)
        if self.type_mode in {'FLOAT', 'INT'}:
            data = [sizes, min_val, max_val]
            if any(not isinstance(v, (float, int)) for v in data):
                sizes, min_val, max_val = ak.broadcast_arrays(*data)
                size = ak.sum(ak.flatten(sizes, axis=None))
                out = rng.random(size)
                out = ak.unflatten(out, sizes)
            else:
                out = rng.random(sizes)
            if self.type_mode == 'FLOAT':
                range_ = max_val - min_val
                out = out * range_ + min_val
            else:
                range_ = max_val - min_val + 1
                out = out * range_ + min_val
                out = ak.values_astype(out, int)

        elif self.type_mode == 'VECTOR':
            if not all(isinstance(v, (float, int))
                       or isinstance(v[0], (float, int))
                       for v in [sizes, min_vec, max_vec]):
                min_vec = min_vec[np.newaxis] \
                    if isinstance(min_vec[0], (float, tuple)) else min_vec
                max_vec = max_vec[np.newaxis] \
                    if isinstance(max_vec[0], (float, tuple)) else max_vec
                sizes, min_vec, max_vec = ak.broadcast_arrays(
                    sizes, min_vec, max_vec, depth_limit=1, right_broadcast=False)
                size = ak.sum(ak.flatten(sizes, axis=None))
                out = rng.random((size, 3), dtype=np.float32)
                out = ak.unflatten(out, sizes)
                range_ = max_vec - min_vec
                out = out * range_[:,np.newaxis] + min_vec[:,np.newaxis]
            else:
                out = rng.random((sizes, 3), dtype=np.float32)
                range_ = max_vec - min_vec
                out = out * range_ + min_vec
        else:
            raise(TypeError(f"Unknown type {self.type_mode=}"))

        out = ak.Array(out)
        self.outputs[0].sv_set(out)


register, unregister = bpy.utils.register_classes_factory([SvRandomArrayNode])
