# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.profile import profile
from sverchok.utils.sv_noise_utils import numpy_perlin_noise

from sverchok_extra.utils import array_math as amath

try:
    import awkward as ak
except ImportError:
    ak = None


class SvArrVectorNoiseNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: array
    Tooltip:
    """
    bl_idname = 'SvArrVectorNoiseNode'
    bl_label = 'Vector Noise (Array)'
    sv_icon = 'SV_ALPHA'

    seed: IntProperty(update=lambda s, c: s.process_node(c))

    def sv_draw_buttons(self, context, layout):
        layout.prop(self, 'seed')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        s = self.inputs.new('SvStringsSocket', 'Scale')
        s.use_prop = True
        s.default_float_property = 1.0
        self.outputs.new('SvVerticesSocket', 'Noise')

    @profile
    def process(self):
        verts = self.inputs['Vertices'].sv_get(deepcopy=False, default=None)
        if verts is None:
            return
        scale = self.inputs['Scale'].sv_get(deepcopy=False)
        scale = scale if self.inputs['Scale'].is_linked else scale[0][0]

        sc_verts1 = verts * scale
        sc_verts2, counts = amath.flatten(sc_verts1, deep=-2)
        sc_verts = ak.to_numpy(sc_verts2)
        noise = np.stack((
            numpy_perlin_noise(sc_verts, self.seed, smooth=True),
            numpy_perlin_noise(sc_verts, self.seed + 1, smooth=True),
            numpy_perlin_noise(sc_verts, self.seed + 2, smooth=True)
        )).T
        noise = amath.unflatten(noise, counts)
        self.outputs[0].sv_set(noise)


register, unregister = bpy.utils.register_classes_factory([SvArrVectorNoiseNode])
