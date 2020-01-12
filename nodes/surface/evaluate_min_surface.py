from sverchok.utils.logging import info, exception

try:
    import scipy
    from scipy.interpolate import Rbf
    scipy_available = True
except ImportError as e:
    info("SciPy is not available, Evaluate MinimalSurface node will not be available")
    scipy_available = False

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level

if scipy_available:

    
    class SvExEvalMinimalSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Evaluate Minimal Surface
        Tooltip: Evaluate Minimal Surface
        """
        bl_idname = 'SvExEvalMinimalSurfaceNode'
        bl_label = 'Evaluate Minimal Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'

        def sv_init(self, context):
            self.inputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'
            self.inputs.new('SvStringsSocket', "TargetU")
            self.inputs.new('SvStringsSocket', "TargetV")
            self.outputs.new('SvVerticesSocket', "Vertices")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            surfaces_s = self.inputs['Surface'].sv_get()
            target_us_s = self.inputs['TargetU'].sv_get()
            target_vs_s = self.inputs['TargetV'].sv_get()

            verts_out = []

            for surface, target_us, target_vs in zip_long_repeat(surfaces_s, target_us_s, target_vs_s):
                new_verts = surface(target_us, target_vs)
                new_verts = new_verts.tolist()
                verts_out.append(new_verts)

            self.outputs['Vertices'].sv_set(verts_out)

def register():
    if scipy_available:
        bpy.utils.register_class(SvExEvalMinimalSurfaceNode)

def unregister():
    if scipy_available:
        bpy.utils.unregister_class(SvExEvalMinimalSurfaceNode)


