
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

    class SvExCylinderSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Cylinder
        Tooltip: Transform Solid cylinder
        """
        bl_idname = 'SvExCylinderSolidNode'
        bl_label = 'Cylinder (Solid)'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'


        cylinder_radius: FloatProperty(
            name="Radius",
            default=1,
            precision=4,
            update=updateNode)
        cylinder_height: FloatProperty(
            name="Height",
            default=1,
            precision=4,
            update=updateNode)
        cylinder_angle: FloatProperty(
            name="Angle",
            default=360,
            precision=4,
            update=updateNode)

        origin: FloatVectorProperty(
            name="Origin",
            default=(0, 0, 0),
            size=3,
            update=updateNode)
        direction: FloatVectorProperty(
            name="Origin",
            default=(0, 0, 1),
            size=3,
            update=updateNode)


        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Radius").prop_name = 'cylinder_radius'
            self.inputs.new('SvStringsSocket', "Height").prop_name = 'cylinder_height'
            self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'origin'
            self.inputs.new('SvVerticesSocket', "Direction").prop_name = 'direction'
            self.inputs.new('SvStringsSocket', "Angle").prop_name = 'cylinder_angle'
            self.outputs.new('SvStringsSocket', "Solid")



        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            p = [s.sv_get()[0] for s in self.inputs]

            solids = []
            for rad, height, origin, direc, angle  in zip(*mlr(p)):
                cylinder = Part.makeCylinder(rad, height, Base.Vector(origin), Base.Vector(direc), angle)
                solids.append(cylinder)

            self.outputs['Solid'].sv_set(solids)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvExCylinderSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvExCylinderSolidNode)
