
import scipy
from scipy.interpolate import Rbf
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat

class SvExMinimalSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Minimal Surface
    Tooltip: Minimal Surface
    """
    bl_idname = 'SvExMinimalSurfaceNode'
    bl_label = 'Minimal Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    functions = [
        ('multiquadric', "Multi Quadric", "Multi Quadric", 0),
        ('inverse', "Inverse", "Inverse", 1),
        ('gaussian', "Gaussian", "Gaussian", 2),
        ('cubic', "Cubic", "Cubic", 3),
        ('quintic', "Quintic", "Qunitic", 4),
        ('thin_plate', "Thin Plate", "Thin Plate", 5)
    ]

    function : EnumProperty(
            name = "Function",
            items = functions,
            default = 'multiquadric',
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvVerticesSocket', "Vertices")

    def draw_buttons(self, context, layout):
        layout.prop(self, "function")

    def process(self):

        if not self.inputs['Vertices'].is_linked:
            return

        if not self.outputs['Vertices'].is_linked:
            return

        vertices_s = self.inputs['Vertices'].sv_get()

        GRID_POINTS = 25

        verts_out = []
        for vertices in vertices_s:
            XYZ = np.array(vertices)
            x_min = XYZ[:,0].min()
            x_max = XYZ[:,0].max()
            y_min = XYZ[:,1].min()
            y_max = XYZ[:,1].max()
            xi = np.linspace(x_min, x_max, GRID_POINTS)
            yi = np.linspace(y_min, y_max, GRID_POINTS)
            XI, YI = np.meshgrid(xi, yi)
            smooth = 0.0
            epsilon = 1.0

            rbf = Rbf(XYZ[:,0],XYZ[:,1],XYZ[:,2],function=self.function,smooth=smooth,epsilon=epsilon)
            ZI = rbf(XI,YI)

            new_verts = np.dstack((XI,YI,ZI)).tolist()
            verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvExMinimalSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExMinimalSurfaceNode)

