# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import numpy_match_long_repeat
import numpy as np

try:
    import awkward as ak
    # import numba as nb
    nb = None
except ImportError:
    ak, nb = None, None

if nb:
    # @nb.jit(nopython=True)
    # def arange(start, stop, step, builder):
    #     for i in range(len(start)):
    #         num = int((stop[i] - start[i]) // step[i])
    #         builder.begin_list()
    #         for j in range(num):
    #             inc = j * step[i]
    #             builder.append(start[i] + inc)
    #         builder.end_list()
    #
    #
    # def _range_step_stop(start, stop, step):
    #     start, stop, step = np.asarray(start), np.asarray(stop), np.asarray(step)
    #     start, stop, step = numpy_match_long_repeat([start, stop, step])
    #     build = ak.ArrayBuilder()
    #     arange(start, stop, step, build)
    #     return build.snapshot()

    #
    # @nb.jit(nopython=True)
    # def arange(start, stop, step):
    #     inp_num = max(len(start), len(stop), len(step))
    #     nums = np.zeros(inp_num+1, dtype=np.int64)
    #     max1, max2, max3 = len(start)-1, len(stop)-1, len(step)-1
    #     for i in range(inp_num):
    #         start_ = start[i] if i <= max1 else start[max1]
    #         stop_ = stop[i] if i <= max2 else stop[max2]
    #         step_ = step[i] if i <= max3 else step[max3]
    #         increment = int((stop_ - start_) // step_)
    #         nums[i+1] = increment
    #     res = np.zeros(np.sum(nums))
    #     current = 0
    #     for i in range(inp_num):
    #         n = nums[i+1]
    #         start_ = start[i] if i <= max1 else start[max1]
    #         step_ = step[i] if i <= max3 else step[max3]
    #         for j in range(n):
    #             res[current] = start_ + (j * step_)
    #             current += 1
    #     return res, np.cumsum(nums)
    #
    #
    # def _range_step_stop(start, stop, step):
    #     start, stop, step = np.asarray(start), np.asarray(stop), np.asarray(step)
    #     res, ind = arange(start, stop, step)
    #     res = ak.contents.NumpyArray(res)
    #     ind = ak.index.Index(ind)
    #     ar = ak.contents.ListOffsetArray(ind, res)
    #     return ak.Array(ar)


    @nb.jit(nopython=True)
    def arange(start, stop, step):
        inp_num = len(start)
        nums = np.zeros(inp_num+1, dtype=np.int64)
        for i in range(inp_num):
            increment = int((stop[i] - start[i]) // step[i])
            nums[i+1] = increment
        res = np.zeros(np.sum(nums))
        current = 0
        for i in range(inp_num):
            n = nums[i+1]
            for j in range(n):
                res[current] = start[i] + (j * step[i])
                current += 1
        return res, np.cumsum(nums)


def _range_(start, stop, step, type_='FLOAT'):
    if all(isinstance(v, (float, int)) for v in (start, stop, step)):
        step = max(1e-5, abs(step))
        if start > stop:
            step = -step
        ar = np.arange(start, stop, step)
    else:
        args = [start, stop, step]
        args = [[v] if isinstance(v, (float, int)) else v for v in args]
        args = [np.asarray(v) for v in args]
        start, stop, step = numpy_match_long_repeat(args)
        res, ind = arange(start, stop, step)
        if type_ == 'INT':
            res = np.asarray(res, dtype=np.int)
        res = ak.contents.NumpyArray(res)
        ind = ak.index.Index(ind)
        ar = ak.contents.ListOffsetArray(ind, res)
    return ak.Array(ar)


def range_(start, stop, step, type_):
    if not all(isinstance(v, (int, float)) for v in [start, stop, step]):
        start, stop, step = ak.broadcast_arrays(start, stop, step)
        step = np.absolute(step)
        step = ak.where(step < 1e-5, 1e-5, step)
        step = ak.where(start > stop, -step, step)
        count = (stop - start) / step
        count = ak.where(count < 0, 0, count)
        count = ak.values_astype(count, int)
        num = ak.sum(count)
        out = np.zeros(num)
        out = ak.unflatten(out, count)
        indexes = ak.local_index(out)
        steps = step * indexes
        return ak.values_astype(out + steps + start, type_)
    else:
        step = max(1e-5, abs(step))
        step = -step if start > stop else step
        return ak.Array(np.arange(start, stop, step, dtype=type_))


def count_range(start, stop, count, type_):
    if not all(isinstance(v, (int, float)) for v in [start, stop, count]):
        start, stop, count = ak.broadcast_arrays(start, stop, count)
        num = ak.sum(count)
        out = np.zeros(num)
        out = ak.unflatten(out, count)
        indexes = ak.local_index(out)
        diff = stop - start
        step = diff / ak.where(count == 1, 1, (count - 1))
        steps = step * indexes
        return ak.values_astype(out + steps + start, type_)
    else:
        return ak.Array(np.linspace(start, stop, num=count, dtype=type_))


def step_range(start, step, count, type_):
    if not all(isinstance(v, (int, float)) for v in [start, step, count]):
        start, step, count = ak.broadcast_arrays(start, step, count)
        num = ak.sum(count)
        out = np.zeros(num)
        out = ak.unflatten(out, count)
        indexes = ak.local_index(out)
        steps = step * indexes
        return ak.values_astype(out + steps + start, type_)
    else:
        stop = start + step * (count - 1)
        return ak.Array(np.linspace(start, stop, num=int(count), dtype=type_))


class SvArrNumberRangeNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrNumberRangeNode'
    bl_label = 'Range Array'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    type_modes = [
        ("INT", "Int", "Integer Series", 0),
        ("FLOAT", "Float", "Float Series", 1),
    ]

    range_modes = [
        ("RANGE", "Range", "Define range by setting start, step and stop.", 0),
        ("COUNT", "Count", "Define range by setting start, stop and count number (divisions).", 1),
        ("STEP", "Step", "Define range by setting start, step and count number", 2),
    ]

    def mode_change(self, context):
        sock_type = 'int' if self.type_mode == 'INT' else 'float'
        self.inputs['Start'].default_property_type = sock_type
        self.inputs['Stop'].default_property_type = sock_type
        self.inputs['Step'].default_property_type = sock_type

        self.inputs['Stop'].enabled = self.range_mode != 'STEP'
        self.inputs['Step'].enabled = self.range_mode != 'COUNT'
        self.inputs['Count'].enabled = self.range_mode != 'RANGE'
        self.process_node(context)

    type_mode: EnumProperty(
        name='Number Type',
        items=type_modes,
        default='FLOAT',
        update=mode_change)

    range_mode: EnumProperty(
        name='Range Mode',
        items=range_modes,
        default='RANGE',
        update=mode_change)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Start").use_prop = True
        s = self.inputs.new('SvStringsSocket', "Stop")
        s.use_prop = True
        s.default_float_property = 10
        s.default_int_property = 10
        s = self.inputs.new('SvStringsSocket', "Step")
        s.use_prop = True
        s.default_float_property = 1
        s.default_int_property = 1
        s = self.inputs.new('SvStringsSocket', "Count")
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 10
        s.enabled = False

        self.outputs.new('SvStringsSocket', "Range")

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, "type_mode", expand=True)
        layout.prop(self, "range_mode", expand=True)

    def process(self):
        start = self.inputs['Start'].sv_get(deepcopy=False)
        start = start if self.inputs['Start'].is_linked else start[0][0]
        stop = self.inputs['Stop'].sv_get(deepcopy=False)
        stop = stop if self.inputs['Stop'].is_linked else stop[0][0]
        step = self.inputs['Step'].sv_get(deepcopy=False)
        step = step if self.inputs['Step'].is_linked else step[0][0]
        count = self.inputs['Count'].sv_get(deepcopy=False)
        count = count if self.inputs['Count'].is_linked else count[0][0]
        type_ = int if self.type_mode == 'INT' else float
        if self.range_mode == 'RANGE':
            res = range_(start, stop, step, type_)
        elif self.range_mode == 'COUNT':
            res = count_range(start, stop, count, type_)
        elif self.range_mode == 'STEP':
            res = step_range(start, step, count, type_)
        else:
            raise(TypeError(f"Unknown type {self.range_mode=}"))
        self.outputs[0].sv_set(res)


register, unregister = bpy.utils.register_classes_factory([SvArrNumberRangeNode])
