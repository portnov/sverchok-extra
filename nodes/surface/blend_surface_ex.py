# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import get_data_nesting_level, updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.surface import SvSurface, SurfaceEdge
from sverchok.utils.surface.blend_optimizer import BlendSurfaceConstraint, BlendSurfaceInput, BlendSurfaceOptimizer

class SvBlendSurfaceExNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Advanced Blend / Fillet Surface
    Tooltip: Advanced version - Generate additional interface surface to blend two surfaces smoothly
    """
    bl_idname = 'SvBlendSurfaceExNode'
    bl_label = 'Blend Surfaces Ex'
    bl_icon = 'SURFACE_DATA'
    sv_icon = 'SV_BLEND_SURFACE'
    sv_dependencies = {'scipy'}

    curve_options = [
            (SurfaceEdge.MIN_U.name, "Min U", "Use surface edge with minimal U parameter value", 0),
            (SurfaceEdge.MAX_U.name, "Max U", "Use surface edge with maximal U parameter value", 1),
            (SurfaceEdge.MIN_V.name, "Min V", "Use surface edge with minimal V parameter value", 2),
            (SurfaceEdge.MAX_V.name, "Max V", "Use surface edge with maximal V parameter value", 3)
        ]

    curve1_mode : EnumProperty(
            name = "Curve 1",
            description = "What curve on the first surface to use",
            items = curve_options,
            default = SurfaceEdge.MIN_U.name,
            update = updateNode)

    curve2_mode : EnumProperty(
            name = "Curve 2",
            description = "What curve on the second surface to use",
            items = curve_options,
            default = SurfaceEdge.MIN_U.name,
            update = updateNode)

    tangency_modes = [
            (BlendSurfaceConstraint.G1.name, "G1 - Tangency", "G1 tangency: match tangent vectors", 0),
            (BlendSurfaceConstraint.NORMALS_MATCH.name, "G2 - Normals Match", "G2 tangency: match tangent vectors, normal vectors", 1)
        ]

    tangency_mode : EnumProperty(
            name = "Smoothness",
            description = "How smooth the tangency should be",
            items = tangency_modes,
            update = updateNode)

    lambda_curvature : FloatProperty(
            name = "Curvature factor",
            min = 0.0,
            default = 0.5,
            update = updateNode)

    lambda_bending : FloatProperty(
            name = "Bending factor",
            min = 0.0,
            default = 0.5,
            update = updateNode)

    tolerance : FloatProperty(
            name = "Tolerance",
            min = 0.0,
            precision = 8,
            default = 1e-5,
            update = updateNode)

    use_cpts : BoolProperty(
            name = "Use conrtol points",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'tangency_mode')
        box = layout.row(align=True)
        box.prop(self, 'curve1_mode', text='')
        box = layout.row(align=True)
        box.prop(self, 'curve2_mode', text='')
        layout.prop(self, 'use_cpts')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'tolerance')

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', 'Surface1')
        self.inputs.new('SvSurfaceSocket', 'Surface2')
        self.inputs.new('SvStringsSocket', 'Curvature').prop_name = 'lambda_curvature'
        self.inputs.new('SvStringsSocket', 'Bending').prop_name = 'lambda_bending'
        self.outputs.new('SvSurfaceSocket', 'Surface')

    def _process(self, surface1, surface2, curvature, bending):
        edge1 = SurfaceEdge[self.curve1_mode]
        edge2 = SurfaceEdge[self.curve2_mode]
        input1 = BlendSurfaceInput(surface1, edge1.direction, edge1.boundary)
        input2 = BlendSurfaceInput(surface2, edge2.direction, edge2.boundary)
        optimizer = BlendSurfaceOptimizer(input1, input2)
        surface = optimizer.solve(
                    constraint = BlendSurfaceConstraint[self.tangency_mode],
                    lambda_bending = bending,
                    lambda_curvature = curvature,
                    use_cpts = self.use_cpts,
                    tolerance = self.tolerance)
        return surface

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surface1_s = self.inputs['Surface1'].sv_get()
        surface2_s = self.inputs['Surface2'].sv_get()
        curvature_s = self.inputs['Curvature'].sv_get()
        bending_s = self.inputs['Bending'].sv_get()

        level1 = get_data_nesting_level(surface1_s, data_types=(SvSurface,))
        level2 = get_data_nesting_level(surface2_s, data_types=(SvSurface,))
        flat_output = level1 < 2 and level2 < 2

        surface1_s = ensure_nesting_level(surface1_s, 2, data_types=(SvSurface,))
        surface2_s = ensure_nesting_level(surface2_s, 2, data_types=(SvSurface,))
        curvature_s = ensure_nesting_level(curvature_s, 2)
        bending_s = ensure_nesting_level(bending_s, 2)

        surfaces_out = []
        for params in zip_long_repeat(surface1_s, surface2_s, curvature_s, bending_s):
            new_surfaces = []
            for surface1, surface2, curvature, bending in zip_long_repeat(*params):
                surface = self._process(surface1, surface2, curvature, bending)
                new_surfaces.append(surface)
            if flat_output:
                surfaces_out.extend(new_surfaces)
            else:
                surfaces_out.append(new_surfaces)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvBlendSurfaceExNode)

def unregister():
    bpy.utils.unregister_class(SvBlendSurfaceExNode)

