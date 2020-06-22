
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
    from mathutils import Vector, Matrix
    from mathutils.geometry import tessellate_polygon as tessellate

    import FreeCAD as F
    import Part
    import Mesh
    from FreeCAD import Base
    from sverchok.data_structure import match_long_repeat as mlr

    def ensure_triangles(coords, indices, handle_concave_quads):
        """
        this fully tesselates the incoming topology into tris,
        not optimized for meshes that don't contain ngons
        """
        new_indices = []
        concat = new_indices.append
        concat2 = new_indices.extend
        for idxset in indices:
            num_verts = len(idxset)
            if num_verts == 3:
                concat(tuple(idxset))
            elif num_verts == 4 and not handle_concave_quads:
                # a b c d  ->  [a, b, c], [a, c, d]
                concat2([(idxset[0], idxset[1], idxset[2]), (idxset[0], idxset[2], idxset[3])])
            else:
                subcoords = [Vector(coords[idx]) for idx in idxset]
                for pol in tessellate([subcoords]):
                    concat([idxset[i] for i in pol])
        return new_indices

    class SvExMeshToSolidNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Mesh to Solid
        Tooltip: Generate solid from closed mesh
        """
        bl_idname = 'SvExMeshToSolidNode'
        bl_label = 'Mesh to Solid'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_VORONOI'


        precision: FloatProperty(
            name="Precision",
            default=0.1,
            precision=4,
            update=updateNode)
        def draw_buttons(self, context, layout):
            layout.prop(self, "precision")

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Verts")
            self.inputs.new('SvStringsSocket', "Faces")
            self.outputs.new('SvStringsSocket', "Solid")


        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            verts_s = self.inputs[0].sv_get(deepcopy=False)
            faces_s = self.inputs[1].sv_get(deepcopy=False)
            solids = []
            faces = []
            for verts, faces in zip(*mlr([verts_s, faces_s])):
                tri_faces = ensure_triangles(verts, faces, True)
                faces_t = []
                for f in tri_faces:
                    faces_t.append([verts[c] for c in f])
                print(faces_t)
                mesh = Mesh.Mesh(faces_t)
                shape = Part.Shape()
                shape.makeShapeFromMesh(mesh.Topology, 0.05)
                solid = Part.makeSolid(shape)
                solids.append(solid)


            self.outputs['Solid'].sv_set(solids)




def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvExMeshToSolidNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvExMeshToSolidNode)
