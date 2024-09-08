# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_mesh_utils import polygons_to_edges
from sverchok_extra.dependencies import shapely

def to_3d(pt):
    if len(pt) == 2:
        return tuple(pt) + (0,)
    else:
        return pt

def triangulate(geometry):
    tris = shapely.delaunay_triangles(geometry)

    vert_idxs = dict()
    idx = 0
    faces = []
    for tri in tris.geoms:
        polys = tri.intersection(geometry)
        if isinstance(polys, shapely.Polygon):
            polys = [polys]
        elif isinstance(polys, shapely.MultiPolygon):
            polys = polys.geoms
        elif isinstance(polys, shapely.GeometryCollection):
            polys = [poly for poly in polys.geoms if isinstance(poly, shapely.Polygon)]
        else:
            polys = []
        for poly in polys:
            if not poly.exterior.is_ccw:
                poly = poly.reverse()
            for pt in poly.exterior.coords:
                i = vert_idxs.get(to_3d(pt), None)
                if i is None:
                    i = idx
                    idx += 1
                    vert_idxs[to_3d(pt)] = i
            face = [vert_idxs[to_3d(pt)] for pt in poly.exterior.coords[:-1]]
            faces.append(face)
    edges = polygons_to_edges([faces], unique_edges=True)[0]
    return list(vert_idxs.keys()), edges, faces

def edges_only(geometry):
    if isinstance(geometry, (shapely.LineString, shapely.LinearRing)):
        geoms = [geometry]
    elif isinstance(geometry, shapely.Polygon):
        geoms = [geometry.exterior]
    elif isinstance(geometry, shapely.MultiLineString):
        geoms = geometry.geoms
    elif isinstance(geometry, shapely.MultiPolygon):
        geoms = [g.exterior for g in geometry.geoms]
    else:
        geoms = []

    vert_idxs = dict()
    idx = 0
    all_edges = []
    for geom in geoms:
        for pt in geom.coords:
            i = vert_idxs.get(to_3d(pt), None)
            if i is None:
                i = idx
                idx += 1
                vert_idxs[to_3d(pt)] = i
        face = [vert_idxs[to_3d(pt)] for pt in geom.coords]
        edges = list(zip(face, face[1:]))
        all_edges.extend(edges)
    return list(vert_idxs.keys()), all_edges, []

def to_mesh(geometry):
    if isinstance(geometry, (shapely.Polygon, shapely.MultiPolygon, shapely.GeometryCollection)):
        return triangulate(geometry)
    else:
        return edges_only(geometry)

def from_mesh(verts, edges, faces):
    verts = [to_3d(v) for v in verts]
    bm = bmesh_from_pydata(verts, edges, faces)
    polygons = []
    for bm_face in bm.faces:
        poly = shapely.Polygon([list(v.co) for v in bm_face.verts])
        polygons.append(poly)
    strings = []
    for bm_edge in bm.edges:
        if bm_edge.is_wire:
            string = shapely.LineString([list(v.co) for v in bm_edge.verts])
            strings.append(string)
    points = []
    for bm_vert in bm.verts:
        if len(bm_vert.link_edges) == 0:
            point = shapely.Point(list(bm_vert.co))
            points.append(point)
    if len(polygons) > 0 and len(strings) == 0 and len(points) == 0:
        return shapely.MultiPolygon(polygons)
    elif len(polygons) == 0 and len(strings) > 0 and len(points) == 0:
        return shapely.MultiLineString(strings)
    elif len(polygons) == 0 and len(strings) == 0 and len(points) > 0:
        return shapely.MultiPoint(points)
    else:
        return shapely.GeometryCollection(polygons + strings + points)

def boundary(geometry):
    if isinstance(geometry, shapely.GeometryCollection):
        polygons = [g for g in geometry.geoms if isinstance(g, (shapely.Polygon, shapely.MultiPolygon))]
        strings = [g for g in geometry.geoms if isinstance(g, (shapely.LineString, shapely.LinearRing, shapely.MultiLineString))]
        poly_bounds = [shapely.boundary(g) for g in polygons]
        string_bounds = [shapely.boundary(g) for g in strings]
        return shapely.GeometryCollection(poly_bounds + string_bounds)
    else:
        return shapely.boundary(geometry)

def union_collection(geometry):
    if isinstance(geometry, (shapely.GeometryCollection, shapely.MultiLineString, shapely.MultiPolygon)):
        return shapely.union_all(list(geometry.geoms))
    else:
        return geometry

