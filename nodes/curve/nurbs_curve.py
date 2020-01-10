
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

if geomdl_available:
    
    class SvExNurbsCurveNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: NURBS Curve
        Tooltip: NURBS Curve
        """
        bl_idname = 'SvExNurbsCurveNode'
        bl_label = 'NURBS Curve'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'

        sample_size : FloatProperty(
                name = "Samples",
                default = 50,
                min = 4,
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "ControlPoints")
            self.inputs.new('SvStringsSocket', "Weights")
            self.inputs.new('SvStringsSocket', "Samples").prop_name = 'sample_size'
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")

        def process(self):
            vertices_s = self.inputs['ControlPoints'].sv_get()
            has_weights = self.inputs['Weights'].is_linked
            weights_s = self.inputs['Weights'].sv_get(default = [[1.0]])
            samples_s = self.inputs['Samples'].sv_get()

            verts_out = []
            edges_out = []
            for vertices, weights, samples in zip_long_repeat(vertices_s, weights_s, samples_s):
                if isinstance(samples, (list, tuple)):
                    samples = samples[0]
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

                # Set evaluation delta (controls the number of curve points)
                curve.sample_size = samples

                # Get curve points (the curve will be automatically evaluated)
                verts_out.append(curve.evalpts)
                new_edges = [(i,i+1) for i in range(len(verts_out[0])-1)]
                edges_out.append(new_edges)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)

def register():
    if geomdl_available:
        bpy.utils.register_class(SvExNurbsCurveNode)

def unregister():
    if geomdl_available:
        bpy.utils.unregister_class(SvExNurbsCurveNode)

