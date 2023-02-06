# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.profile import profile
from sverchok_extra.utils import array_math as amath

try:
    import awkward as ak
except ImportError:
    ak = None


class SvArrSubdividePolylineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrSubdividePolylineNode'
    bl_label = 'Subdivide Polyline (Array)'
    sv_icon = 'SV_ALPHA'
    sv_dependencies = ['awkward']

    interpolations = [
        ('LINEAR', 'Linear', '', 0),
        ('CUBIC', 'Cubic', '', 1),
        ('CATMULL_ROM', 'Catmull-Rom', '', 2),
    ]

    interpolation: EnumProperty(items=interpolations,
                                update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'interpolation', text='')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Array')
        s = self.inputs.new('SvStringsSocket', 'Cuts')
        s.use_prop = True
        s.default_property_type = 'int'
        s.default_int_property = 10
        self.outputs.new('SvStringsSocket', 'Array')

    @profile
    def process(self):
        line = self.inputs[0].sv_get(deepcopy=False, default=None)
        if line is None:
            return
        cuts = self.inputs[1].sv_get(deepcopy=False)
        cuts = ak.values_astype(cuts, int) if self.inputs[1].is_linked \
            else ak.Array([max(cuts[0]+[0])])

        new_verts = amath.subdivide_polyline(line.verts, cuts, self.interpolation)
        new_edges = amath.connect_polyline(new_verts)
        new_line = ak.Array({'verts': new_verts, 'edges': new_edges})
        self.outputs[0].sv_set(new_line)


register, unregister = bpy.utils.register_classes_factory([SvArrSubdividePolylineNode])
