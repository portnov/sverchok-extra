
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, ensure_nesting_level
from sverchok.utils.logging import info, exception

from sverchok_extra.data.surface import SvExGeomdlSurface
from sverchok_extra.data.curve import SvExGeomdlCurve
from sverchok_extra.dependencies import geomdl

if geomdl is not None:
    from geomdl import BSpline, NURBS, tessellate, trimming

    def point_to_2d(point, plane):
        if plane == 'XY':
            return point[0], point[1]
        elif plane == 'YZ':
            return point[1], point[2]
        elif plane == 'XZ':
            return point[0], point[2]
        else:
            raise Exception("Unsupported plane")

    def geomdl_curve_to_2d(curve, plane):
        if isinstance(curve, NURBS.Curve):
            new_curve = NURBS.Curve()
        elif isinstance(curve, BSpline.Curve):
            new_curve = BSpline.Curve()
        else:
            raise TypeError("Unsupported curve type: %s" % type(curve))

        #new_curve.dimension = 2
        new_curve.degree = curve.degree
        new_curve.ctrlpts = [point_to_2d(point, plane) for point in curve.ctrlpts]
        print(new_curve.ctrlpts)
        if isinstance(curve, NURBS.Curve):
            new_curve.weights = curve.weights
        new_curve.knotvector = curve.knotvector

        return new_curve

    class SvExTessellateTrimmedNurbsNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Tessellate trimmed NURBS Surface
        Tooltip: Tessellate a NURBS Surface trimmed by NURBS curve(s)
        """
        bl_idname = 'SvExTessellateTrimmedNurbsNode'
        bl_label = 'Tessellate NURBS Surface'
        bl_icon = 'SURFACE_NSURFACE'

        sample_size_u : IntProperty(
                name = "Samples U",
                default = 25,
                min = 4,
                update = updateNode)

        sample_size_v : IntProperty(
                name = "Samples V",
                default = 25,
                min = 4,
                update = updateNode)

        planes = [
            ('XY', "XY", "XOY plane", 0),
            ('YZ', "YZ", "YOZ plane", 1),
            ('XZ', "XZ", "XOZ plane", 2)
        ]

        trim_plane : EnumProperty(
            name = "Trim Plane",
            items = planes,
            default = 'XY',
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.label(text="Trim curves plane:")
            layout.prop(self, "trim_plane", expand=True)

        def sv_init(self, context):
            self.inputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'
            self.inputs.new('SvExCurveSocket', "TrimCurves").display_shape = 'DIAMOND'
            self.inputs.new('SvStringsSocket', "SamplesU").prop_name = 'sample_size_u'
            self.inputs.new('SvStringsSocket', "SamplesV").prop_name = 'sample_size_v'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Faces")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curve_s = self.inputs['TrimCurves'].sv_get()
            surface_s = self.inputs['Surface'].sv_get()
            samples_u_s = self.inputs['SamplesU'].sv_get()
            samples_v_s = self.inputs['SamplesV'].sv_get()

            verts_out = []
            faces_out = []
            for curves, surface, samples_u, samples_v in zip_long_repeat(curve_s, surface_s, samples_u_s, samples_v_s):
                if not isinstance(surface, SvExGeomdlSurface):
                    raise TypeError("This node supports NURBS surfaces only, but got %s!" % type(surface))
                if isinstance(samples_u, (list, tuple)):
                    samples_u = samples_u[0]
                if isinstance(samples_v, (list, tuple)):
                    samples_v = samples_v[0]

                if not isinstance(curves, (list, tuple)):
                    curves = [curves]

                trim_curves = []
                for curve in curves:
                    if not isinstance(curve, SvExGeomdlCurve):
                        raise TypeError("This node supports NURBS curves only, but got %s!" % type(curve))
                    trim = geomdl_curve_to_2d(curve.curve, self.trim_plane)
                    trim_curves.append(trim)

                surface.surface.trims = trim_curves
                trimming.fix_trim_curves(surface.surface)
                surface.surface.tessellator = tessellate.TrimTessellate()
                surface.surface.sample_size_u = samples_u
                surface.surface.sample_size_v = samples_v
                surface.surface.tessellate()

                new_verts = [vert.data for vert in surface.surface.vertices]
                new_faces = [f.data for f in surface.surface.faces]
                verts_out.append(new_verts)
                faces_out.append(new_faces)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Faces'].sv_set(faces_out)

def register():
    if geomdl is not None:
        bpy.utils.register_class(SvExTessellateTrimmedNurbsNode)

def unregister():
    if geomdl is not None:
        bpy.utils.unregister_class(SvExTessellateTrimmedNurbsNode)

