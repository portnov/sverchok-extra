
import numpy as np
from math import ceil

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.surface import SvSurface

from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.integrate import solve_ivp

def solve_euler(surface, p0, max_t, negate=False, step=None, direction='MAX'):
    u_min, u_max, v_min, v_max = surface.get_domain()
    t = 0.0
    uvs = p0[:,:2]
    m = len(p0)
    n = ceil(max_t / step)
    result = np.zeros((n, m, 2))
    i = 0
    while t <= max_t:
        calculator = surface.curvature_calculator(uvs[:,0], uvs[:,1], order=True)
        data = calculator.calc(need_uv_directions = True, need_matrix=False)
        if direction == 'MAX':
            directions = data.principal_direction_2_uv
        else:
            directions = data.principal_direction_1_uv
        if negate:
            directions = - directions

        uvs += directions * step
        uvs = np.clip(uvs, [u_min,v_min], [u_max, v_max])
        #if (uvs[:,0] < u_min).any() or (uvs[:,0] > u_max).any() or (uvs[:,1] < v_min).any() or (uvs[:,1] > v_max).any():
        #    break
        result[i] = uvs
        i += 1
        t += step
    return result

def solve_lines(surface, p0, tf, method='RK45', negate=False, step=None, direction='MAX'):

    if method == 'EULER':
        return solve_euler(surface, p0, tf, negate=negate, step=step, direction=direction)

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

class SvExSurfaceCurvatureLinesNode(SverchCustomTreeNode, bpy.types.Node):
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
        ('EULER', "Euler", "Euler", 0),
        ('RK45', "Runge-Kutta 5(4)", "Runge-Kutta 5(4)", 1),
        ('RK23', "Runge-Kutta 3(2)", "Runge-Kutta 3(2)", 2),
        ('DOP853', "Runge-Kutta 8(7)", "Runge-Kutta 8(7)", 3),
        ('Radau', "Implicit Runge-Kutta", "Implicit Runge-Kutta - Radau IIA 5", 4),
        ('BDF', "Backward differentiation", "Implicit multi-step variable-order (1 to 5) method based on a backward differentiation formula for the derivative approximation", 5),
        ('LSODA', "Adams / BDF", "Adams/BDF method with automatic stiffness detection and switching", 6)
    ]

    method : EnumProperty(
        name = "Method",
        items = methods,
        default = 'EULER',
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
                if self.method == 'EULER':
                    new_uv = solve_euler(surface, np.array(src_points),
                                max_t,
                                negate = self.negate,
                                step = step,
                                direction = self.direction)
                    print(f"New_uv: {new_uv.shape}")
                    us_i, vs_i = new_uv[:,:,0], new_uv[:,:,1]
                    for us, vs in zip(us_i, vs_i):
                        new_verts = surface.evaluate_array(us, vs).tolist()
                        uv_out.append(new_uv.tolist())
                        verts_out.append(new_verts)
                else:
                    for src_point in src_points:
                        u0,v0,_ = src_point
                        #print(step)
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

