# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.utils.geom import PlaneEquation

class SvProjectMatrixNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Project Matrix Plane
    Tooltip: Project a Matrix onto a Plane
    """
    bl_idname = 'SvProjectMatrixNode'
    bl_label = 'Project Matrix to Plane'
    bl_icon = 'CURVE_NCURVE'

    def update_sockets(self, context):
        self.inputs['PlaneMatrix'].hide_safe = self.plane_mode != 'MATRIX'
        self.inputs['Point'].hide_safe = self.plane_mode != 'NORMAL'
        self.inputs['Normal'].hide_safe = self.plane_mode != 'NORMAL'
        updateNode(self, context)

    plane_modes = [
            ('MATRIX', "Matrix", "Matrix", 0),
            ('NORMAL', "Point and Normal", "Point and Normal", 1)
        ]
    
    plane_mode : EnumProperty(
            name = "Plane input",
            items = plane_modes,
            default = 'MATRIX',
            update = update_sockets)

    normal: FloatVectorProperty(
        name="Normal",
        default=(0, 0, 1),
        size=3,
        update=updateNode)

    point: FloatVectorProperty(
        name="Point",
        default=(0, 0, 1),
        size=3,
        update=updateNode)

    axes = [
            ('X', "X", "X axis", 0),
            ('Y', "Y", "Y axis", 1),
            ('Z', "Z", "Z axis", 2)
        ]

    direction_axis : EnumProperty(
        name = "Direction axis",
        description = "Projection direction",
        items = axes,
        default = 'Z',
        update = updateNode)

    track_axis : EnumProperty(
        name = "Track axis",
        items = axes,
        default = 'X',
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvMatrixSocket', "Matrix")
        self.inputs.new('SvMatrixSocket', "PlaneMatrix")
        self.inputs.new('SvVerticesSocket', "Point").prop_name = 'point'
        self.inputs.new('SvVerticesSocket', "Normal").prop_name = 'normal'
        self.outputs.new('SvMatrixSocket', "Matrix")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text="Direction axis:")
        layout.prop(self, 'direction_axis', expand=True)
        layout.label(text="Track axis:")
        layout.prop(self, 'track_axis', expand=True)
        layout.label(text="Define plane by:")
        layout.prop(self, 'plane_mode', text='')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        matrix_in = self.inputs['Matrix'].sv_get()

        point_in = self.inputs['Point'].sv_get()
        normal_in = self.inputs['Normal'].sv_get()

        if self.plane_mode == 'MATRIX':
            plane_matrix_in = self.inputs['PlaneMatrix'].sv_get()
        else:
            plane_matrix_in = [None]

        matrix_out = []
        for matrix, plane_matrix, point, normal in zip_long_repeat(matrix_in, plane_matrix_in, point_in, normal_in):
            if self.plane_mode == 'MATRIX':
                plane = PlaneEquation.from_matrix(plane_matrix, normal_axis='Z')
            else:
                plane = PlaneEquation.from_normal_and_point(normal, point)
            matrix = plane.projection_of_matrix(matrix,
                        direction_axis = self.direction_axis,
                        track_axis = self.track_axis)
            matrix_out.append(matrix)

        self.outputs['Matrix'].sv_set(matrix_out)

def register():
    bpy.utils.register_class(SvProjectMatrixNode)

def unregister():
    bpy.utils.unregister_class(SvProjectMatrixNode)

