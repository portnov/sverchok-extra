
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.field.scalar import SvScalarField

def solve(field, init, iso_value, step_coeff, maxiter=30, threshold=1e-4):

    i = 0
    p = init
    while True:
        i += 1
        v = field.evaluate_grid(p[:,0], p[:,1], p[:,2]) - iso_value
        dv = abs(v)
        #print(f"I#{i}, DV {dv.max()}")
        if (dv < threshold).all():
            return p
        if i > maxiter:
            raise Exception(f"Maximum number of iterations ({maxiter}) is exceeded, last error {dv.max()}")
        gradX, gradY, gradZ = field.gradient_grid(p[:,0], p[:,1], p[:,2])
        grad = np.stack((gradX, gradY, gradZ)).T
        n = np.linalg.norm(grad, axis=1, keepdims=True)**2
        step = step_coeff * v[np.newaxis].T * grad / n
        p -= step

class SvExImplSurfaceSolverNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Implicit Surface Wrap
    Tooltip: Wrap points onto the implicit surface
    """
    bl_idname = 'SvExImplSurfaceSolverNode'
    bl_label = 'Implicit Surface Wrap'
    bl_icon = 'OUTLINER_OB_EMPTY'

    iso_value : FloatProperty(
            name = "Iso Value",
            default = 0.0,
            update = updateNode)

    maxiter : IntProperty(
            name = "Max Iterations",
            default = 30,
            min = 2,
            update = updateNode)

    accuracy : IntProperty(
            name = "Accuracy",
            default = 4,
            min = 1,
            update = updateNode)

    step : FloatProperty(
            name = "Step",
            description = "Step coefficient",
            min = 0.0,
            default = 1.0,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'maxiter')
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "Field")
        p = self.inputs.new('SvVerticesSocket', "Vertices")
        p.use_prop = True
        p.prop = (0.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', 'IsoValue').prop_name = 'iso_value'
        self.inputs.new('SvStringsSocket', 'Step').prop_name = 'step'
        self.outputs.new('SvVerticesSocket', 'Vertices')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        field_s = self.inputs['Field'].sv_get()
        verts_s = self.inputs['Vertices'].sv_get()
        iso_value_s = self.inputs['IsoValue'].sv_get()
        step_s = self.inputs['Step'].sv_get()

        field_s = ensure_nesting_level(field_s, 2, data_types=(SvScalarField,))
        verts_s = ensure_nesting_level(verts_s, 4)
        iso_value_s = ensure_nesting_level(iso_value_s, 2)
        step_s = ensure_nesting_level(step_s, 2)

        verts_out = []

        threshold = 10**(-self.accuracy)

        for params in zip_long_repeat(field_s, verts_s, iso_value_s, step_s):
            for field, verts, iso_value, step in zip_long_repeat(*params):
                verts = np.array(verts)
                new_verts = solve(field, verts, iso_value, step, maxiter = self.maxiter, threshold=threshold).tolist()
                verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvExImplSurfaceSolverNode)

def unregister():
    bpy.utils.unregister_class(SvExImplSurfaceSolverNode)

