
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

    class SvExSolidBooleanNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Ladybug location
        Tooltip: Generate location from latitude and longitude coordinates
        """
        bl_idname = 'SvExSolidBooleanNode'
        bl_label = 'Solid Boolean'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'


        precision: FloatProperty(
            name="Length",
            default=0.1,
            precision=4,
            update=updateNode)
        mode_options = [
            ("ITX", "Intersect", "", 0),
            ("UNION", "Union", "", 1),
            ("DIFF", "Difference", "", 2)
            ]

        selected_mode: EnumProperty(
            name='Operation',
            items=mode_options,
            description="basic booleans using solids",
            default="ITX",
            update=updateNode)

        def update_mode(self, context):
            self.inputs['Solid A'].hide_safe = self.nest_objs
            self.inputs['Solid B'].hide_safe = self.nest_objs
            self.inputs['Solids'].hide_safe = not self.nest_objs
            updateNode(self, context)

        nest_objs: BoolProperty(
            name="accumulate nested",
            description="bool first two solids, then applies rest to result one by one",
            default=False,
            update=update_mode)
            
        def draw_buttons(self, context, layout):
            layout.prop(self, "selected_mode", toggle=True)
            layout.prop(self, "nest_objs", toggle=True)

        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Solid A")
            self.inputs.new('SvStringsSocket', "Solid B")
            self.inputs.new('SvStringsSocket', "Solids")
            self.inputs['Solids'].hide_safe = True


            self.outputs.new('SvStringsSocket', "Solid")



        def single_union(self):
            solids_a = self.inputs[0].sv_get()
            solids_b = self.inputs[1].sv_get()
            solids = []
            for solid_a, solid_b in zip(*mlr([solids_a, solids_b])):
                solids.append(solid_a.fuse(solid_b))
            self.outputs[0].sv_set(solids)

        def multi_union(self):
            solids = self.inputs[2].sv_get()
            base = solids[0].copy()
            for s in solids[1:]:
                base = base.fuse(s)

            self.outputs[0].sv_set([base])
        def single_intersect(self):
            solids_a = self.inputs[0].sv_get()
            solids_b = self.inputs[1].sv_get()
            solids = []
            for solid_a, solid_b in zip(*mlr([solids_a, solids_b])):
                solids.append(solid_a.common(solid_b))
            self.outputs[0].sv_set(solids)

        def multi_intersect(self):
            solids = self.inputs[2].sv_get()
            base = solids[0].copy()
            for s in solids[1:]:
                base = base.common(s)
        def single_difference(self):
            solids_a = self.inputs[0].sv_get()
            solids_b = self.inputs[1].sv_get()
            solids = []
            for solid_a, solid_b in zip(*mlr([solids_a, solids_b])):
                solids.append(solid_a.cut(solid_b))
            self.outputs[0].sv_set(solids)

        def multi_difference(self):
            solids = self.inputs[2].sv_get()
            base = solids[0].copy()
            for s in solids[1:]:
                base = base.cut(s)

            self.outputs[0].sv_set([base])

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            if self.selected_mode == 'UNION':
                if self.nest_objs:
                    self.multi_union()
                else:
                    self.single_union()
            elif self.selected_mode == 'ITX':
                if self.nest_objs:
                    self.multi_intersect()
                else:
                    self.single_intersect()
            else:
                if self.nest_objs:
                    self.multi_difference()
                else:
                    self.single_difference()


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvExSolidBooleanNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvExSolidBooleanNode)
