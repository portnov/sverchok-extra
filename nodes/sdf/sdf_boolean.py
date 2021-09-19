import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.dummy_nodes import add_dummy
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is None:
    add_dummy('SvExSdfBooleanNode', "SDF Boolean", 'sdf')

class SvExSdfBooleanNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Boolean
    Tooltip: SDF Boolean
    """
    bl_idname = 'SvExSdfBooleanNode'
    bl_label = 'SDF Boolean'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOLID_BOOLEAN'

    operations = [
            ('UNION', "Union", "Union", 0),
            ('INTERSECTION', "Intersection", "Intersection", 1),
            ('DIFFERENCE', "Difference", "Difference", 2)
        ]

    operation : EnumProperty(
            name = "Operation",
            items = operations,
            default = 'UNION',
            update = updateNode)

    k_value : FloatProperty(
            name = "K Value",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    def update_sockets(self, context):
        self.inputs['SDF1'].hide_safe = self.accumulate_nested
        self.inputs['SDF2'].hide_safe = self.accumulate_nested
        self.inputs['SDFs'].hide_safe = not self.accumulate_nested

    accumulate_nested : BoolProperty(
            name = "Accumulate Nested",
            default = False,
            update = update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF1")
        self.inputs.new('SvScalarFieldSocket', "SDF2")
        self.inputs.new('SvScalarFieldSocket', "SDFs")
        self.inputs.new('SvStringsSocket', "KValue").prop_name = 'k_value'
        self.outputs.new('SvScalarFieldSocket', "SDF")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'operation')
        layout.prop(self, 'accumulate_nested')

    def _accumulate(self, sdfs, k):
        if self.operation == 'UNION':
            op = union
        elif self.operation == 'INTERSECTION':
            op = intersection
        else:
            op = difference

        if not sdfs:
            return sdfs

        result = sdfs[0]
        for sdf in sdfs[1:]:
            result = op(result, sdf, k=k)

        return result

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        ks_s = self.inputs['KValue'].sv_get()
        ks_s = ensure_nesting_level(ks_s, 2)

        sdf_out = []

        if not self.accumulate_nested:
            sdf1_s = self.inputs['SDF1'].sv_get()
            sdf2_s = self.inputs['SDF2'].sv_get()

            input_level = get_data_nesting_level(sdf1_s, data_types=(SvScalarField,))
            flat_output = input_level == 1
            sdf1_s = ensure_nesting_level(sdf1_s, 2, data_types=(SvScalarField,))
            sdf2_s = ensure_nesting_level(sdf2_s, 2, data_types=(SvScalarField,))

            for params in zip_long_repeat(sdf1_s, sdf2_s, ks_s):
                new_sdf = []
                for sdf1, sdf2, k in zip_long_repeat(*params):
                    sdf1 = scalar_field_to_sdf(sdf1, 0)
                    sdf2 = scalar_field_to_sdf(sdf2, 0)
                    if self.operation == 'UNION':
                        sdf = union(sdf1, sdf2, k=k)
                    elif self.operation == 'INTERSECTION':
                        sdf = intersection(sdf1, sdf2, k=k)
                    else:
                        sdf = difference(sdf1, sdf2, k=k)
                    field = SvExSdfScalarField(sdf)
                    new_sdf.append(field)
                if flat_output:
                    sdf_out.extend(new_sdf)
                else:
                    sdf_out.append(new_sdf)

        else:
            sdfs_s = self.inputs['SDFs'].sv_get()
            sdfs_s = ensure_nesting_level(sdfs_s, 3, data_types=(SvScalarField,))

            for params in zip_long_repeat(sdfs_s, ks_s):
                new_sdf = []
                for sdfs, k in zip_long_repeat(*params):
                    sdfs = [scalar_field_to_sdf(f, 0) for f in sdfs]
                    sdf = self._accumulate(sdfs, k)
                    field = SvExSdfScalarField(sdf)
                    new_sdf.append(field)
                sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfBooleanNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfBooleanNode)

