import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *
from sverchok.utils.sv_bmesh_utils import remove_doubles

if sdf is not None:
    from sdf import *
    from sdf import core as sdf_core
    BATCH_SIZE = sdf.core.BATCH_SIZE
else:
    BATCH_SIZE = 1

class SvExSdfGenerateNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: SDF Generate Mesh
    Tooltip: SDF Generate Mesh
    """
    bl_idname = 'SvExSdfGenerateNode'
    bl_label = 'SDF Generate Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_MCUBES'
    sv_dependencies = {'sdf'}

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
        default = 0.05,
        precision = 8,
        update = updateNode)

    samples : IntProperty(
        name = "Samples",
        min = 100,
        default = 1*1000*1000,
        update = updateNode)

    def update_sockets(self, context):
        self.inputs['Step'].hide_safe = self.precision_mode != 'STEP'
        self.inputs['Samples'].hide_safe = self.precision_mode != 'SAMPLES'
        updateNode(self, context)

    precision_modes = [
            ('STEP', "Step", "Step", 0),
            ('SAMPLES', "Samples", "Samples", 1)
        ]

    precision_mode : EnumProperty(
        name = "Precision mode",
        items = precision_modes,
        default = 'STEP',
        update = update_sockets)

    specify_workers : BoolProperty(
        name = "Specify workers count",
        default = False,
        update = updateNode)

    workers_count : IntProperty(
        name = "Workers count",
        min = 1,
        default = 4,
        update = updateNode)

    batch_size : IntProperty(
        name = "Batch size",
        min = 1,
        default = BATCH_SIZE,
        update = updateNode)
    
    sparse : BoolProperty(
        name = "Sparse",
        default = True,
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'precision_mode')
        layout.prop(self, 'remove_doubles')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'threshold')
        layout.prop(self, 'specify_workers')
        if self.specify_workers:
            layout.prop(self, 'workers_count')
        layout.prop(self, 'batch_size')
        layout.prop(self, 'sparse')

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvStringsSocket', "Step").prop_name = 'step'
        self.inputs.new('SvStringsSocket', "Samples").prop_name = 'samples'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Faces")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        step_s = self.inputs['Step'].sv_get()
        samples_s = self.inputs['Samples'].sv_get()

        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        step_s = ensure_nesting_level(step_s, 2)
        samples_s = ensure_nesting_level(samples_s, 2)

        verts_out = []
        faces_out = []
        for params in zip_long_repeat(sdf_s, step_s, samples_s):
            new_verts = []
            new_faces = []
            for sdf, step, samples in zip_long_repeat(*params):
                sdf = scalar_field_to_sdf(sdf, 0)

                if self.precision_mode == 'STEP':
                    samples = sdf_core.SAMPLES
                else:
                    step = None

                if self.specify_workers:
                    workers = self.workers
                else:
                    workers = sdf_core.WORKERS

                print(f"Step={step}, samples={samples}")

                points = sdf.generate(step=step, samples=samples,
                            workers = workers, batch_size = self.batch_size,
                            sparse = self.sparse)

                res = geometry_from_points(points)
                
                verts = res.verts
                faces = res.tris

                if self.remove_doubles:
                    verts, _, faces = remove_doubles(verts, [], faces, self.threshold)

                new_verts.append(verts)
                new_faces.append(faces)

            verts_out.append(new_verts)
            faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Faces'].sv_set(faces_out)


def register():
    bpy.utils.register_class(SvExSdfGenerateNode)


def unregister():
    bpy.utils.unregister_class(SvExSdfGenerateNode)
