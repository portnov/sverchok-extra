# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import IntProperty, EnumProperty
from sverchok.data_structure import fixed_iter

from sverchok.node_tree import SverchCustomTreeNode
from sverchok_extra.utils import array_math as amath

try:
    import awkward as ak
except ImportError:
    ak = None


class SvSliceArrayNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvSliceArrayNode'
    bl_label = 'Slice Array'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    slice_types = [
        ('START', 'Start', ''),
        ('STOP', 'Stop', ''),
        ('STEP', 'Step', ''),
    ]

    def update_slice_type(self, context):
        self.inputs['Start'].enabled = 'START' in self.slice_type
        self.inputs['Stop'].enabled = 'STOP' in self.slice_type
        self.inputs['Step'].enabled = 'STEP' in self.slice_type
        self.process_node(context)

    slice_type: EnumProperty(
        items=slice_types,
        default={'STOP'},
        options={'ENUM_FLAG'},
        update=update_slice_type)
    axis: IntProperty(update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'slice_type', expand=True, text=None)
        layout.prop(self, 'axis')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        s = self.inputs.new('SvStringsSocket', 'Start')
        s.use_prop = True
        s.default_property_type = 'int'
        s.enabled = False
        s = self.inputs.new('SvStringsSocket', 'Stop')
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 1
        s = self.inputs.new('SvStringsSocket', 'Step')
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 1
        s.enabled = False
        self.outputs.new('SvStringsSocket', 'Data')

    def sv_update(self):
        in_s = self.inputs[0]
        out_type = 'SvStringsSocket' if not in_s.is_linked else in_s.other.bl_idname
        if self.outputs[0].bl_idname != out_type:
            self.outputs[0].replace_socket(out_type)

    def process(self):
        data = self.inputs[0].sv_get(deepcopy=False, default=None)
        if data is None:
            return
        s1, s2, s3 = self.inputs['Start'], self.inputs['Stop'], self.inputs['Step']
        start = s1.sv_get(deepcopy=False)
        start = start if s1.is_linked else start[0][0]
        start = start if s1.enabled else None
        stop = s2.sv_get(deepcopy=False)
        stop = stop if s2.is_linked else stop[0][0]
        stop = stop if s2.enabled else None
        step = s3.sv_get(deepcopy=False)
        step = step if s3.is_linked else step[0][0]
        step = step if s3.enabled else None

        if any(s.enabled and s.is_linked for s in self.inputs[1:]):
            start = start if s1.is_linked and s1.enabled else [start]
            stop = stop if s2.is_linked and s2.enabled else [stop]
            step = step if s3.is_linked and s3.enabled else [step]
            num = max(len(v) for v in [start, stop, step])
            sss = [fixed_iter(start, num), fixed_iter(stop, num), fixed_iter(step, num)]
            sl = []
            for sa, so, se in zip(*sss):
                sl.append(slice(sa, so, se))
            sl = tuple(sl)
        else:
            sl = amath.slices(slice(start, stop, step), axis=self.axis)
        data = data[sl]
        self.outputs[0].sv_set(data)


register, unregister = bpy.utils.register_classes_factory([SvSliceArrayNode])
