import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is not None:
    from sdf import *

class SvExSdfSlabNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF Slab
    Tooltip: SDF Slab
    """
    bl_idname = 'SvExSdfSlabNode'
    bl_label = 'SDF Slab'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_dependencies = {'sdf'}

    def update_sockets(self, context):
        self.inputs['MinX'].hide_safe = not self.use_x_min
        self.inputs['MaxX'].hide_safe = not self.use_x_max
        self.inputs['MinY'].hide_safe = not self.use_y_min
        self.inputs['MaxY'].hide_safe = not self.use_y_max
        self.inputs['MinZ'].hide_safe = not self.use_z_min
        self.inputs['MaxZ'].hide_safe = not self.use_z_max
        updateNode(self, context)

    use_x_min : BoolProperty(
        name = "Min X",
        default = True,
        update=update_sockets)

    use_x_max : BoolProperty(
        name = "Max X",
        default = True,
        update=update_sockets)

    use_y_min : BoolProperty(
        name = "Min Y",
        default = True,
        update=update_sockets)

    use_y_max : BoolProperty(
        name = "Max Y",
        default = True,
        update=update_sockets)

    use_z_min : BoolProperty(
        name = "Min Z",
        default = True,
        update=update_sockets)

    use_z_max : BoolProperty(
        name = "Max Z",
        default = True,
        update=update_sockets)

    x_min : FloatProperty(
        name = "Min X",
        default = -1.0,
        update=updateNode)

    x_max : FloatProperty(
        name = "Max X",
        default = 1.0,
        update=updateNode)

    y_min : FloatProperty(
        name = "Min Y",
        default = -1.0,
        update=updateNode)

    y_max : FloatProperty(
        name = "Max Y",
        default = 1.0,
        update=updateNode)

    z_min : FloatProperty(
        name = "Min Z",
        default = -1.0,
        update=updateNode)

    z_max : FloatProperty(
        name = "Max Z",
        default = 1.0,
        update=updateNode)

    flat_output : BoolProperty(
        name = "Flat output",
        default = True,
        update=updateNode)

    def draw_buttons(self, context, layout):
        box = layout.column(align=True)

        row = box.row(align=True)
        row.prop(self, 'use_x_min', toggle=True)
        row.prop(self, 'use_x_max', toggle=True)

        row = box.row(align=True)
        row.prop(self, 'use_y_min', toggle=True)
        row.prop(self, 'use_y_max', toggle=True)

        row = box.row(align=True)
        row.prop(self, 'use_z_min', toggle=True)
        row.prop(self, 'use_z_max', toggle=True)

        layout.prop(self, 'flat_output')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "MinX").prop_name = 'x_min'
        self.inputs.new('SvStringsSocket', "MaxX").prop_name = 'x_max'
        self.inputs.new('SvStringsSocket', "MinY").prop_name = 'y_min'
        self.inputs.new('SvStringsSocket', "MaxY").prop_name = 'y_max'
        self.inputs.new('SvStringsSocket', "MinZ").prop_name = 'z_min'
        self.inputs.new('SvStringsSocket', "MaxZ").prop_name = 'z_max'
        self.outputs.new('SvScalarFieldSocket', "SDF")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        x_min_s = self.inputs['MinX'].sv_get()
        x_max_s = self.inputs['MaxX'].sv_get()
        y_min_s = self.inputs['MinY'].sv_get()
        y_max_s = self.inputs['MaxY'].sv_get()
        z_min_s = self.inputs['MinZ'].sv_get()
        z_max_s = self.inputs['MaxZ'].sv_get()

        x_min_s = ensure_nesting_level(x_min_s, 2)
        x_max_s = ensure_nesting_level(x_max_s, 2)
        y_min_s = ensure_nesting_level(y_min_s, 2)
        y_max_s = ensure_nesting_level(y_max_s, 2)
        z_min_s = ensure_nesting_level(z_min_s, 2)
        z_max_s = ensure_nesting_level(z_max_s, 2)

        fields_out = []
        for params in zip_long_repeat(x_min_s, x_max_s, y_min_s, y_max_s, z_min_s, z_max_s):
            new_fields = []
            for x_min, x_max, y_min, y_max, z_min, z_max in zip_long_repeat(*params):

                if not self.use_x_min:
                    x_min = None
                if not self.use_x_max:
                    x_max = None
                if not self.use_y_min:
                    y_min = None
                if not self.use_y_max:
                    y_max = None
                if not self.use_z_min:
                    z_min = None
                if not self.use_z_max:
                    z_max = None
                print(f"X {x_min} - {x_max}, Y {y_min} - {y_max}, Z {z_min} - {z_max}")

                sdf = slab(x0=x_min, y0=y_min, z0=z_min, x1=x_max, y1=y_max, z1=z_max)
                field = SvExSdfScalarField(sdf)
                new_fields.append(field)
            if self.flat_output:
                fields_out.extend(new_fields)
            else:
                fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfSlabNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfSlabNode)

