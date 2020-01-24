from sverchok.utils.logging import info, exception

try:
    from geomdl import NURBS
    from geomdl import tessellate
    from geomdl import knotvector
    geomdl_available = True
except ImportError as e:
    info("SciPy is not available, Evaluate MinimalSurface node will not be available")
    info("geomdl package is not available, NURBS Surface node will not be available")
    geomdl_available = False

import numpy as np

import bpy
from bpy.props import EnumProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level

if geomdl_available:

    class SvExEvalNurbsSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Evaluate NURBS Surface
        Tooltip: Evaluate NURBS Surface
        """
        bl_idname = 'SvExEvalNurbsSurfaceNode'
        bl_label = 'Evaluate NURBS Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'

        @throttled
        def update_sockets(self, context):
            self.inputs['U'].hide_safe = self.input_mode == 'VERTICES'
            self.inputs['V'].hide_safe = self.input_mode == 'VERTICES'
            self.inputs['Vertices'].hide_safe = self.input_mode == 'PAIRS'

        input_modes = [
            ('PAIRS', "Separate", "Separate U V (or X Y) sockets", 0),
            ('VERTICES', "Vertices", "Single socket for vertices", 1)
        ]

        input_mode : EnumProperty(
            name = "Input mode",
            items = input_modes,
            default = 'PAIRS',
            update = update_sockets)

        axes = [
            ('XY', "X Y", "XOY plane", 0),
            ('YZ', "Y Z", "YOZ plane", 1),
            ('XZ', "X Z", "XOZ plane", 2)
        ]

        orientation : EnumProperty(
                name = "Orientation",
                items = axes,
                default = 'XY',
                update = updateNode)

        def draw_buttons(self, context, layout):
            layout.label(text="Input mode:")
            layout.prop(self, "input_mode", expand=True)
            if self.input_mode == 'VERTICES':
                layout.label(text="Input orientation:")
                layout.prop(self, "orientation", expand=True)

        def sv_init(self, context):
            self.inputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND' #0
            self.inputs.new('SvStringsSocket', "U") # 1
            self.inputs.new('SvStringsSocket', "V") # 2
            self.inputs.new('SvVerticesSocket', "Vertices") # 3
            self.outputs.new('SvVerticesSocket', "Vertices") # 0
            self.update_sockets(context)

        def parse_input(self, verts):
            verts = np.array(verts)
            if self.orientation == 'XY':
                us, vs = verts[:,0], verts[:,1]
            elif self.orientation == 'YZ':
                us, vs = verts[:,1], verts[:,2]
            else: # XZ
                us, vs = verts[:,0], verts[:,2]

            # Rescale U and V coordinates to [0, 1]
            min_u = us.min()
            min_v = vs.min()
            max_u = us.max()
            max_v = vs.max()

            size_u = max_u - min_u
            size_v = max_v - min_v

            if size_u < 0.00001:
                raise Exception("Object has too small size in U direction")
            if size_v < 0.00001:
                raise Exception("Object has too small size in V direction")

            us = (us - min_u) / size_u
            vs = (vs - min_v) / size_v
            return us.tolist(), vs.tolist()

        def build_output(self, surface, XI, YI, ZI):
            if surface.input_orientation == 'X':
                YI, ZI, XI = XI, YI, ZI
            elif surface.input_orientation == 'Y':
                ZI, XI, YI = XI, YI, ZI
            else: # Z
                pass
            verts = np.dstack((XI, YI, ZI))
            if surface.has_matrix:
                verts = verts - surface.input_matrix.translation
                np_matrix = np.array(surface.input_matrix.to_3x3())
                verts = np.apply_along_axis(lambda v : np_matrix @ v, 2, verts)
            return verts

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            surfaces_s = self.inputs['Surface'].sv_get()
            target_us_s = self.inputs['U'].sv_get(default=[[]])
            target_vs_s = self.inputs['V'].sv_get(default=[[]])
            target_verts_s = self.inputs['Vertices'].sv_get(default = [[]])

            verts_out = []

            inputs = zip_long_repeat(surfaces_s, target_us_s, target_vs_s, target_verts_s)
            for surface, target_us, target_vs, target_verts in inputs:
                if self.input_mode == 'VERTICES':
                    target_us, target_vs = self.parse_input(target_verts)
                else:
                    pass

                #self.info("Us: %s, Vs: %s", target_us, target_vs)
                new_verts = surface.evaluate_list(list(zip(target_us, target_vs)))

                verts_out.append(new_verts)

            self.outputs['Vertices'].sv_set(verts_out)

def register():
    if geomdl_available:
        bpy.utils.register_class(SvExEvalNurbsSurfaceNode)

def unregister():
    if geomdl_available:
        bpy.utils.unregister_class(SvExEvalNurbsSurfaceNode)

