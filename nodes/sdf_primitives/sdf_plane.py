import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.dummy_nodes import add_dummy
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *

if sdf is None:
    add_dummy('SvExSdfPlaneNode', "SDF Hemispace", 'sdf')
else:
    from sdf import *

class SvExSdfPlaneNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Hemispace
    Tooltip: SDF Hemispace
    """
    bl_idname = 'SvExSdfPlaneNode'
    bl_label = 'SDF Hemispace'
    bl_icon = 'OUTLINER_OB_EMPTY'

    origin: FloatVectorProperty(
        name="Origin",
        default=(0, 0, 0),
        size=3,
        update=updateNode)

    normal: FloatVectorProperty(
        name="Normal",
        default=(0, 0, 1),
        size=3,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
        self.inputs.new('SvVerticesSocket', "Normal").prop_name = 'normal'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        origins_s = self.inputs['Origin'].sv_get()
        normal_s = self.inputs['Normal'].sv_get()

        origins_s = ensure_nesting_level(origins_s, 3)
        normal_s = ensure_nesting_level(normal_s, 3)

        fields_out = []
        for params in zip_long_repeat(origins_s, normal_s):
            new_fields = []
            for origin, normal in zip_long_repeat(*params):
                sdf = plane(normal=normal, point=origin)
                field = SvExSdfScalarField(sdf)
                new_fields.append(field)
            fields_out.append(new_fields)

        self.outputs['SDF'].sv_set(fields_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfPlaneNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfPlaneNode)

