
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok_extra.data.curve import SvExCurve
from sverchok_extra.data.surface import SvExExtrudeCurveCurveSurface

class SvExExtrudeCurveCurveSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Extrude Curve along Curve
    Tooltip: Generate a surface by extruding a curve along another curve
    """
    bl_idname = 'SvExExtrudeCurveCurveSurfaceNode'
    bl_label = 'Extrude Curve Along Curve'
    bl_icon = 'MOD_THICKNESS'

    def sv_init(self, context):
        self.inputs.new('SvExCurveSocket', "Profile").display_shape = 'DIAMOND'
        self.inputs.new('SvExCurveSocket', "Extrusion").display_shape = 'DIAMOND'
        self.outputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        profile_s = self.inputs['Profile'].sv_get()
        extrusion_s = self.inputs['Extrusion'].sv_get()

        if isinstance(profile_s[0], SvExCurve):
            profile_s = [profile_s]
        if isinstance(extrusion_s[0], SvExCurve):
            extrusion_s = [extrusion_s]

        surface_out = []
        for profiles, extrusions in zip_long_repeat(profile_s, extrusion_s):
            for profile, extrusion in zip_long_repeat(profiles, extrusions):
                surface = SvExExtrudeCurveCurveSurface(profile, extrusion)
                surface_out.append(surface)

        self.outputs['Surface'].sv_set(surface_out)

def register():
    bpy.utils.register_class(SvExExtrudeCurveCurveSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExExtrudeCurveCurveSurfaceNode)

