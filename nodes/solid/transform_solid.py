
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty
import bmesh
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.sv_mesh_utils import polygons_to_edges, mesh_join
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata
from sverchok.utils.logging import info, exception

from sverchok_extra.dependencies import FreeCAD

if FreeCAD is not None:
    import FreeCAD as F
    import Part
    from FreeCAD import Base
    from sverchok.data_structure import match_long_repeat as mlr

    class SvExTransformSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Apply Matrix to Solid
        Tooltip: Transform Solid with Matrix
        """
        bl_idname = 'SvExTransformSolidNode'
        bl_label = 'Transform Solid'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'


        precision: FloatProperty(
            name="Precision",
            default=0.1,
            precision=4,
            update=updateNode)
        # def draw_buttons(self, context, layout):
        #     layout.prop(self, "join", toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Solid")
            self.inputs.new('SvMatrixSocket', "Matrix")
            self.outputs.new('SvStringsSocket', "Solid")




        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids_in = self.inputs[0].sv_get()
            matrixes = self.inputs[1].sv_get()
            solids = []
            for solid, matrix in zip(*mlr([solids_in, matrixes])):
                myMat = Base.Matrix(*[i for v in matrix for i in v])
                solid_o = solid.transformGeometry(myMat)
                solids.append(solid_o)


            self.outputs['Solid'].sv_set(solids)



def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvExTransformSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvExTransformSolidNode)
