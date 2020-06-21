
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface

from sverchok_extra.dependencies import scipy
from scipy.integrate import solve_ivp

def solve_lines(surface, p0, tf, method='RK45', negate=False, step=None, direction='MAX'):

    def f(t, ps):
        #print("P:", ps.shape)
        us = ps[0,:]
        vs = ps[1,:]
        calculator = surface.curvature_calculator(us, vs, order=True)
        data = calculator.calc(need_uv_directions = True, need_matrix=False)
        if direction == 'MAX':
            directions = data.principal_direction_2_uv
        else:
            directions = data.principal_direction_1_uv
        if negate:
            directions = - directions
        return directions

    kwargs = dict()
    if step is not None:
        kwargs['first_step'] = step
        kwargs['max_step'] = step
    res = solve_ivp(f, (0, tf), p0, method=method, vectorized=True, **kwargs)

    if not res.success:
        raise Exception("Can't solve the equation: " + res.message)
    return res.y.T

class SvExSurfaceCurvatureLinesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Curvature Lines
    Tooltip: Generate surface principal curvature lines
    """
    bl_idname = 'SvExSurfaceCurvatureLinesNode'
    bl_label = 'Surface Curvature Lines'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EVAL_SURFACE'

    directions = [
        ('MIN', "Minimum", "Minimum principal curvature direction", 0),
        ('MAX', "Maximum", "Maximum principal curvature direction", 1)
    ]

    direction : EnumProperty(
            name = "Direction",
            items = directions,
            default = 'MIN',
            update = updateNode)

    max_t : FloatProperty(
            name = "MaxT",
            min = 0.0,
            default = 1.0,
            update = updateNode)

    negate : BoolProperty(
            name = "Negate",
            description = "Go to the opposite direction",
            default = False,
            update = updateNode)

    methods = [
        ('RK45', "Runge-Kutta 5(4)", "Runge-Kutta 5(4)", 0),
        ('RK23', "Runge-Kutta 3(2)", "Runge-Kutta 3(2)", 1),
        ('DOP853', "Runge-Kutta 8(7)", "Runge-Kutta 8(7)", 2),
        ('Radau', "Implicit Runge-Kutta", "Implicit Runge-Kutta - Radau IIA 5", 3),
        ('BDF', "Backward differentiation", "Implicit multi-step variable-order (1 to 5) method based on a backward differentiation formula for the derivative approximation", 4),
        ('LSODA', "Adams / BDF", "Adams/BDF method with automatic stiffness detection and switching", 5)
    ]

    method : EnumProperty(
        name = "Method",
        items = methods,
        default = 'RK45',
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'method')
        layout.prop(self, 'direction', expand=True)
        layout.prop(self, 'negate', toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        p = self.inputs.new('SvVerticesSocket', "UVPoints")
        p.use_prop = True
        p.prop = (0.5, 0.5, 0.0)
        self.inputs.new('SvStringsSocket', 'Step')
        self.inputs.new('SvStringsSocket', 'MaxT').prop_name = 'max_t'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvVerticesSocket', "UVPoints")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
        src_point_s = self.inputs['UVPoints'].sv_get()
        src_point_s = ensure_nesting_level(src_point_s, 4)
        step_s = self.inputs['Step'].sv_get(default = [[None]])
        maxt_s = self.inputs['MaxT'].sv_get()

        has_step = self.inputs['Step'].is_linked

        verts_out = []
        uv_out = []
        inputs = zip_long_repeat(surfaces_s, src_point_s, step_s, maxt_s)
        for surfaces, src_point_i, step_i, maxt_i in inputs:
            for surface, src_points, step, max_t in zip_long_repeat(surfaces, src_point_i, step_i, maxt_i):
                for src_point in src_points:
                    u0,v0,_ = src_point
                    print(step)
                    new_uv = solve_lines(surface, np.array([u0,v0]),
                                    max_t,
                                    method = self.method,
                                    negate = self.negate,
                                    step = step,
                                    direction = self.direction)
                    us, vs = new_uv[:,0], new_uv[:,1]
                    new_verts = surface.evaluate_array(us, vs).tolist()
                    uv_out.append(new_uv.tolist())
                    verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['UVPoints'].sv_set(uv_out)

def register():
    bpy.utils.register_class(SvExSurfaceCurvatureLinesNode)

def unregister():
    bpy.utils.unregister_class(SvExSurfaceCurvatureLinesNode)

