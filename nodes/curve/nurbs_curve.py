
from sverchok.utils.logging import info, exception

try:
    from geomdl import NURBS
    from geomdl import utilities
    geomdl_available = True
except ImportError as e:
    info("geomdl package is not available, NURBS Curve node will not be available")
    geomdl_available = False

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList

from sverchok_extra.data.curve import SvExGeomdlCurve

if geomdl_available:
    
    class SvExNurbsCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: NURBS Curve
        Tooltip: NURBS Curve
        """
        bl_idname = 'SvExNurbsCurveNode'
        bl_label = 'NURBS Curve'
        bl_icon = 'CURVE_NCURVE'

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "ControlPoints")
            self.inputs.new('SvStringsSocket', "Weights")
            self.outputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['ControlPoints'].sv_get()
            has_weights = self.inputs['Weights'].is_linked
            weights_s = self.inputs['Weights'].sv_get(default = [[1.0]])

            curves_out = []
            for vertices, weights in zip_long_repeat(vertices_s, weights_s):
                fullList(weights, len(vertices))

                # Create a 3-dimensional B-spline Curve
                curve = NURBS.Curve()

                # Set degree
                curve.degree = 3

                # Set control points (weights vector will be 1 by default)
                # Use curve.ctrlptsw is if you are using homogeneous points as Pw
                curve.ctrlpts = vertices
                if has_weights:
                    curve.weights = weights

                # Set knot vector
                curve.knotvector = utilities.generate_knot_vector(curve.degree, len(curve.ctrlpts))

                curve = SvExGeomdlCurve(curve)
                curves_out.append(curve)

            self.outputs['Curve'].sv_set(curves_out)

def register():
    if geomdl_available:
        bpy.utils.register_class(SvExNurbsCurveNode)

def unregister():
    if geomdl_available:
        bpy.utils.unregister_class(SvExNurbsCurveNode)

