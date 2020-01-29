
from sverchok.utils.logging import info, exception

try:
    from geomdl import fitting
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
    
    class SvExInterpolateNurbsCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: NURBS Curve
        Tooltip: Interpolate NURBS Curve
        """
        bl_idname = 'SvExInterpolateNurbsCurveNode'
        bl_label = 'Interpolate NURBS Curve'
        bl_icon = 'CURVE_NCURVE'

        degree : IntProperty(
                name = "Degree",
                min = 2, max = 6,
                default = 3,
                update = updateNode)

        centripetal : BoolProperty(
                name = "Centripetal",
                default = False,
                update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'centripetal', toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
            self.outputs.new('SvExCurveSocket', "Curve").display_shape = 'DIAMOND'
            self.outputs.new('SvVerticesSocket', "ControlPoints")
            self.outputs.new('SvStringsSocket', "Knots")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Vertices'].sv_get()
            degree_s = self.inputs['Degree'].sv_get()

            curves_out = []
            points_out = []
            knots_out = []
            for vertices, degree in zip_long_repeat(vertices_s, degree_s):
                if isinstance(degree, (tuple, list)):
                    degree = degree[0]

                curve = fitting.interpolate_curve(vertices, degree, centripetal=self.centripetal)

                points_out.append(curve.ctrlpts)
                knots_out.append(curve.knotvector)

                curve = SvExGeomdlCurve(curve)
                curves_out.append(curve)

            self.outputs['Curve'].sv_set(curves_out)
            self.outputs['ControlPoints'].sv_set(points_out)
            self.outputs['Knots'].sv_set(knots_out)

def register():
    if geomdl_available:
        bpy.utils.register_class(SvExInterpolateNurbsCurveNode)

def unregister():
    if geomdl_available:
        bpy.utils.unregister_class(SvExInterpolateNurbsCurveNode)

