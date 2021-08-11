
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import bvhtree

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.field.vector import SvVectorField
from sverchok.utils.surface import SvSurface
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExVFieldLinesOnSurfNode', "Vector Field Lines on Surface", 'scipy')
else:
    from scipy.integrate import solve_ivp

    def solve_lines(surface, field, p0, max_t = None, step = None, iterations=None, method='RK45', rotate=False):

        def do_step(ps):
            #print("P:", ps)
            us = ps[0,:]
            vs = ps[1,:]

            derivs = surface.derivatives_data_array(us, vs)
            du = derivs.du
            dv = derivs.dv

            xs = derivs.points[:,0]
            ys = derivs.points[:,1]
            zs = derivs.points[:,2]

            vxs, vys, vzs = field.evaluate_grid(xs,ys,zs)
            vecs = np.stack((vxs, vys, vzs)).T

            vec_u = (vecs * du).sum(axis=1)
            vec_v = (vecs * dv).sum(axis=1)

            if rotate:
                vec_u, vec_v = -vec_v, vec_u

            res = np.array([vec_u, vec_v])
            #print("R:", res)
            return res

        def f(t, ps):
            return do_step(ps)

        def solve_lines_euler():
            points = np.array([p0]).T
            result = [points]
            for i in range(iterations):
                grad = do_step(points)
                points = points + step * grad
                result.append(points)
            result = np.array(result)
            result = np.transpose(result, axes=(2,0,1))[0]
            #print("R", result.shape)
            return result

        if method == 'EULER':
            return solve_lines_euler()

        res = solve_ivp(f, (0, max_t), p0, method=method, vectorized=True)

        if not res.success:
            raise Exception("Can't solve the equation: " + res.message)
        result = rs.y.T
        #print("R", result.shape)
        return result

    class SvExVFieldLinesOnSurfNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Vector Field lines on Surface
        Tooltip: Vector Field lines on Surface
        """
        bl_idname = 'SvExVFieldLinesOnSurfNode'
        bl_label = 'Vector Field Lines on Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'

        def update_sockets(self, context):
            self.inputs['MaxT'].hide_safe = self.method == 'EULER'
            self.inputs['Step'].hide_safe = self.method != 'EULER'
            self.inputs['Iterations'].hide_safe = self.method != 'EULER'
            updateNode(self, context)

        methods = [
            ('EULER', "Euler", "Simplest Euler method", 0),
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
            update = update_sockets)

        cograd : BoolProperty(
            name = "Iso lines",
            default = False,
            update = updateNode)

        max_t : FloatProperty(
            name = "Max T",
            default = 2.0,
            update = updateNode)

        step : FloatProperty(
            name = "Step",
            min = 0.0,
            default = 0.01,
            update = updateNode)

        iterations : IntProperty(
            name = "Iterations",
            min = 0,
            default = 100,
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'method')
            layout.prop(self, 'cograd')

        def sv_init(self, context):
            self.inputs.new('SvVectorFieldSocket', 'Field')
            self.inputs.new('SvSurfaceSocket', 'Surface')
            self.inputs.new('SvVerticesSocket', 'StartUV')
            self.inputs.new('SvStringsSocket', 'MaxT').prop_name = 'max_t'
            self.inputs.new('SvStringsSocket', 'Step').prop_name = 'step'
            self.inputs.new('SvStringsSocket', 'Iterations').prop_name = 'iterations'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvVerticesSocket', "UVPoints")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            start_s = self.inputs['StartUV'].sv_get()
            field_s = self.inputs['Field'].sv_get()
            surface_s = self.inputs['Surface'].sv_get()
            maxt_s = self.inputs['MaxT'].sv_get()
            step_s = self.inputs['Step'].sv_get()
            iterations_s = self.inputs['Iterations'].sv_get()

            start_s = ensure_nesting_level(start_s, 3)
            field_s = ensure_nesting_level(field_s, 2, data_types=(SvVectorField,))
            surface_s = ensure_nesting_level(surface_s, 2, data_types=(SvSurface,))
            maxt_s = ensure_nesting_level(maxt_s, 2)
            step_s = ensure_nesting_level(step_s, 2)
            iterations_s = ensure_nesting_level(iterations_s, 2)

            verts_out = []
            uv_out = []
            for params in zip_long_repeat(start_s, field_s, surface_s, maxt_s, step_s, iterations_s):
                for start, field, surface, max_t, step, iterations in zip_long_repeat(*params):
                    u0, v0, _ = start
                    uvs = solve_lines(surface, field, np.array([u0,v0]),
                                max_t = max_t,
                                step = step,
                                iterations = iterations,
                                method=self.method,
                                rotate = self.cograd)
                    self.debug(f"Start {(u0,v0)} => {len(uvs)} points")
                    us = uvs[:,0]
                    vs = uvs[:,1]
                    #print("U", us)
                    new_uvs = [(u,v,0) for u,v in zip(us,vs)]
                    new_verts = surface.evaluate_array(us, vs).tolist()

                    verts_out.append(new_verts)
                    uv_out.append(new_uvs)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['UVPoints'].sv_set(uv_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExVFieldLinesOnSurfNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExVFieldLinesOnSurfNode)

