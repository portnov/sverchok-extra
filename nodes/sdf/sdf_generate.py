import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.dummy_nodes import add_dummy
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *
from sverchok.utils.sv_bmesh_utils import remove_doubles

if sdf is None:
    add_dummy('SvExSdfGenerateNode', "SDF Generate Mesh", 'sdf')
else:
    from sdf import *

class SvExSdfGenerateNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SDF Generate Mesh
    Tooltip: SDF Generate Mesh
    """
    bl_idname = 'SvExSdfGenerateNode'
    bl_label = 'SDF Generate Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'

    remove_doubles : BoolProperty(
        name = "Remove doubles",
        default = True,
        update = updateNode)

    threshold : FloatProperty(
        name = "Threshold",
        default = 1e-6,
        precision = 8,
        update = updateNode)

    step : FloatProperty(
        name = "Step",
        default = 0.01,
        precision = 8,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'remove_doubles')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'threshold')

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvStringsSocket', "Step").prop_name = 'step'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        step_s = self.inputs['Step'].sv_get()

        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        step_s = ensure_nesting_level(step_s, 2)

        verts_out = []
        faces_out = []
        for params in zip_long_repeat(sdf_s, step_s):
            new_verts = []
            new_faces = []
            for sdf, step in zip_long_repeat(*params):
                sdf = scalar_field_to_sdf(sdf, 0)
                points = sdf.generate(step=step)
                res = geometry_from_points(points)
                
                verts = res.verts
                faces = res.tris

                if self.remove_doubles:
                    verts, _, faces = remove_doubles(verts, [], faces, self.threshold)

                new_verts.extend(verts)
                new_faces.extend(faces)

            verts_out.append(new_verts)
            faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfGenerateNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfGenerateNode)


