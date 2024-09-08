
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok_extra.dependencies import shapely
from sverchok_extra.utils.shapely import to_mesh

class SvExShapelyTriangulateNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: 2D Triangulate
    Tooltip: 2D Triangulate
    """
    bl_idname = 'SvExShapelyTriangulateNode'
    bl_label = '2D Geometry to Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DELAUNAY'
    sv_dependencies = {'shapely'}

    def sv_init(self, context):
        self.inputs.new('SvGeom2DSocket', "Geometry")
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        geometry_s = self.inputs['Geometry'].sv_get()
        input_level = get_data_nesting_level(geometry_s, data_types=(shapely.Geometry,))
        flat_output = input_level == 1
        geometry_s = ensure_nesting_level(geometry_s, 2, data_types=(shapely.Geometry,))

        verts_out = []
        edges_out = []
        faces_out = []
        for params in geometry_s:
            new_verts = []
            new_edges = []
            new_faces = []
            for geometry in params:
                verts, edges, faces = to_mesh(geometry)
                new_verts.append(verts)
                new_edges.append(edges)
                new_faces.append(faces)
            if flat_output:
                verts_out.extend(new_verts)
                edges_out.extend(new_edges)
                faces_out.extend(new_faces)
            else:
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvExShapelyTriangulateNode)

def unregister():
    bpy.utils.unregister_class(SvExShapelyTriangulateNode)

