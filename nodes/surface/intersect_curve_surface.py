
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.surface import SvSurface

from sverchok_extra.dependencies import scipy
from sverchok_extra.utils.geom import intersect_curve_surface

if scipy is not None:

    class SvExCrossCurveSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Intersect Curve Surface
        Tooltip: Intersect Curve Surface
        """
        bl_idname = 'SvExCrossCurveSurfaceNode'
        bl_label = 'Intersect Curve with Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EVAL_SURFACE'

        samples : IntProperty(
            name = "Init Resolution",
            default = 10,
            min = 3,
            update = updateNode)

        methods = [
            ('hybr', "Hybrd & Hybrj", "Use MINPACK’s hybrd and hybrj routines (modified Powell method)", 0),
            ('lm', "Levenberg-Marquardt", "Levenberg-Marquardt algorithm", 1),
            ('krylov', "Krylov", "Krylov algorithm", 2),
            ('broyden1', "Broyden 1", "Broyden1 algorithm", 3),
            ('broyden2', "Broyden 2", "Broyden2 algorithm", 4),
            ('anderson', 'Anderson', "Anderson algorithm", 5),
            ('df-sane', 'DF-SANE', "DF-SANE method", 6)
        ]

        raycast_method : EnumProperty(
            name = "Raycast Method",
            items = methods,
            default = 'hybr',
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'samples')

        def draw_buttons_ext(self, context, layout):
            self.draw_buttons(context, layout)
            layout.prop(self, 'raycast_method')

        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvSurfaceSocket', "Surface")
            self.outputs.new('SvVerticesSocket', "Point")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            surfaces_s = self.inputs['Surface'].sv_get()
            surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
            curves_s = self.inputs['Curve'].sv_get()
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))

            points_out = []
            for surfaces, curves in zip_long_repeat(surfaces_s, curves_s):
                for surface, curve in zip_long_repeat(surfaces, curves):
                    result = intersect_curve_surface(curve, surface,
                                raycast_samples = self.samples,
                                ortho_samples = self.samples,
                                raycast_method = self.raycast_method
                            )
                    new_points = [result]
                    points_out.append(new_points)

            self.outputs['Point'].sv_set(points_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExCrossCurveSurfaceNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExCrossCurveSurfaceNode)

