# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from collections import defaultdict
import numpy as np

from mathutils import Vector, Matrix
import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import zip_long_repeat, ensure_nesting_level, updateNode, throttle_and_update_node
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.freecad import SvFreeCadCurve, SvFreeCadNurbsCurve, curve_to_freecad_nurbs
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import SvSolidFaceSurface, is_solid_face_surface, surface_to_freecad
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvSolidWaffleNode', 'Solid Waffle', 'FreeCAD')
else:
    import Part
    from FreeCAD import Base

    from sverchok.utils.solid import SvSolidTopology, SvGeneralFuse

def matrix_z(matrix):
    location = matrix.translation
    z = matrix @ Vector((0,0,1)) - location
    return z

def make_sections(solid, matrix_a, zs_a, matrix_b, zs_b):
    normal_a = Base.Vector(matrix_z(matrix_a))
    normal_b = Base.Vector(matrix_z(matrix_b))
    slice_wires_a = solid.slices(normal_a, zs_a).Wires
    slice_wires_b = solid.slices(normal_b, zs_b).Wires

    slice_faces_a = [Part.Face(wire) for wire in slice_wires_a]
    slice_faces_b = [Part.Face(wire) for wire in slice_wires_b]

    return slice_faces_a, slice_faces_b

def bisect_wire(solid, matrix):
    location = matrix.translation
    norm = (matrix @ Vector((0,0,1))) - location
    dist = norm.dot(location)
    wires = solid.slice(Base.Vector(norm), dist)
    return wires

def bisect_face(solid, matrix):
    wires = bisect_wire(solid, matrix)
    return Part.Face(wires)

def do_split_many(solids, split_face, select):
    fuse = SvGeneralFuse([split_face] + solids)
    mids_1, mids_2 = [], []
    for mid_parts in fuse.map[1:]:
        #print("M", mid_parts[0].Shells)
        if len(mid_parts) != 2:
            raise Exception(f"The surface does not cut the intersection of solids in 2 parts; result is {mid_parts}")
        mid_1, mid_2 = mid_parts
        c1, c2 = mid_1.CenterOfMass, mid_2.CenterOfMass
        select = Base.Vector(*select)
        d1, d2 = select.dot(c1), select.dot(c2)
        if d1 > d2:
            mid_2, mid_1 = mid_1, mid_2
        mids_1.append(mid_1)
        mids_2.append(mid_2)
    return mids_1, mids_2

def do_waffel(solid, matrix_a, matrix_b, zs_a, zs_b, thickness, split_face, select):
    sections_a, sections_b = make_sections(solid, matrix_a, zs_a, matrix_b, zs_b)
    n_a = len(sections_a)
    all_sections = sections_a + sections_b
    cyls = []
    cyl_idx = 0
    cyls_per_section = defaultdict(list)
    half_cyls1, half_cyls2 = [], []
    for i, section_a in enumerate(sections_a):
        for j, section_b in enumerate(sections_b):
            r = section_a.section(section_b)
            if not r.Compounds[0].Edges:
                continue
            intersection_edge = r.Compounds[0].Edges[0]
            start = intersection_edge.Curve.value(intersection_edge.FirstParameter)
            end = intersection_edge.Curve.value(intersection_edge.LastParameter)
            #print(f"{i}+{j} => {start} - {end}")
            direction = end - start
            start = start - thickness * direction
            end = end + thickness * direction
            height = direction.Length + 2*thickness*direction.Length
            direction.normalize()
            if split_face is not None:
                cylinder = Part.makeCylinder(thickness/2.0, height, start, direction)
                cyls.append(cylinder)
            else:
                half1 = Part.makeCylinder(thickness/2.0, height/2.0, start, direction)
                mid = 0.5*start + 0.5*end
                half2 = Part.makeCylinder(thickness/2.0, height/2.0, mid, direction)
                half_cyls1.append(half1)
                half_cyls2.append(half2)

            cyls_per_section[i].append(cyl_idx)
            cyls_per_section[j].append(cyl_idx)
            cyl_idx += 1

    if split_face is not None:
        half_cyls1, half_cyls2 = do_split_many(cyls, split_face, select)
    
    result_a = []
    for i, section_a in enumerate(sections_a):
        half_cyls = [half_cyls1[k] for k in cyls_per_section[i]]
        part = section_a.cut(half_cyls)
        face = part.Faces[0]
        surface = SvSolidFaceSurface(face)
        result_a.append(surface)

    result_b = []
    for j, section_b in enumerate(sections_b):
        half_cyls = [half_cyls2[k] for k in cyls_per_section[j]]
        part = section_b.cut(half_cyls)
        face = part.Faces[0]
        surface = SvSolidFaceSurface(face)
        result_b.append(surface)
    
    return result_a, result_b

class SvSolidWaffleNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Solid Waffle
    Tooltip: Generate waffle-like structure from a Solid object
    """
    bl_idname = 'SvSolidWaffleNode'
    bl_label = 'Solid Waffle'
    bl_icon = 'OUTLINER_OB_EMPTY'
    solid_catergory = "Operators"

    split_modes = [
            ('HALF', "Even", "Split in the middle of each intersection", 0),
            ('MATRIX', "Matrix", "Split along XY plane of specified matrix", 1),
            ('SURFACE', "Surface", "Split along specified surface", 2)
        ]
    
    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['SplitMatrix'].hide_safe = self.split_mode != 'MATRIX'
        self.inputs['SplitSurface'].hide_safe = self.split_mode != 'SURFACE'

    split_mode : EnumProperty(
            name = "Split mode",
            items = split_modes,
            default = 'HALF',
            update = update_sockets)

    thickness : FloatProperty(
            name = "Thickness",
            default = 0.1,
            min = 0.0,
            update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvMatrixSocket', "MatrixA")
        self.inputs.new('SvMatrixSocket', "MatrixB")
        self.inputs.new('SvStringsSocket', "ZValuesA")
        self.inputs.new('SvStringsSocket', "ZValuesB")
        self.inputs.new('SvMatrixSocket', "SplitMatrix")
        self.inputs.new('SvSurfaceSocket', "SplitSurface")
        self.inputs.new('SvStringsSocket', "Thickness").prop_name = 'thickness'
        self.outputs.new('SvSurfaceSocket', "FacesA")
        self.outputs.new('SvSurfaceSocket', "FacesB")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'split_mode')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids_in = self.inputs['Solid'].sv_get(deepcopy=False)
        matrix_a_in = self.inputs['MatrixA'].sv_get()
        matrix_b_in = self.inputs['MatrixB'].sv_get()
        zs_a_in = self.inputs['ZValuesA'].sv_get()
        zs_b_in = self.inputs['ZValuesB'].sv_get()
        split_matrix_in = self.inputs['SplitMatrix'].sv_get(default=[[None]])
        split_surface_in = self.inputs['SplitSurface'].sv_get(default=[[None]])
        thickness_in = self.inputs['Thickness'].sv_get()

        solids_in = ensure_nesting_level(solids_in, 2, data_types=(Part.Shape,))
        matrix_a_in = ensure_nesting_level(matrix_a_in, 2, data_types=(Matrix,))
        matrix_b_in = ensure_nesting_level(matrix_b_in, 2, data_types=(Matrix,))
        zs_a_in = ensure_nesting_level(zs_a_in, 3)
        zs_b_in = ensure_nesting_level(zs_b_in, 3)
        if self.inputs['SplitMatrix'].is_linked:
            split_matrix_in = ensure_nesting_level(split_matrix_in, 2, data_types=(Matrix,))
        if self.inputs['SplitSurface'].is_linked:
            split_surface_in = ensure_nesting_level(split_surface_in, 2, data_types=(SvSurface,))

        face_a_out = []
        face_b_out = []
        for inputs in zip_long_repeat(solids_in, matrix_a_in, matrix_b_in, zs_a_in, zs_b_in, split_matrix_in, split_surface_in, thickness_in):
            new_face_a = []
            new_face_b = []
            for solid, matrix_a, matrix_b, zs_a, zs_b, split_matrix, split_surface, thickness in zip_long_repeat(*inputs):
                select = matrix_z(matrix_a).cross(matrix_z(matrix_b))
                select = tuple(select)
                if self.split_mode == 'HALF':
                    split_face = None
                elif self.split_mode == 'MATRIX':
                    split_face = bisect_face(solid, split_matrix)
                else:
                    split_face = surface_to_freecad(split_surface, make_face=True).face

                result_a, result_b = do_waffel(solid, matrix_a, matrix_b, zs_a, zs_b, thickness, split_face, select)    
                new_face_a.append(result_a)
                new_face_b.append(result_b)
            face_a_out.append(new_face_a)
            face_b_out.append(new_face_b)

        self.outputs['FacesA'].sv_set(face_a_out)
        self.outputs['FacesB'].sv_set(face_b_out)

def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidWaffleNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidWaffleNode)

