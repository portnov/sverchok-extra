
import numpy as np
from collections import defaultdict
from mathutils import Matrix, Vector
from mathutils import noise
from mathutils import kdtree
from mathutils import bvhtree

from sverchok.utils.logging import info, exception

from sverchok_extra.dependencies import geomdl

if geomdl is not None:
    from geomdl import operations

##################
#                #
#  Surfaces      #
#                #
##################

class SvExSurface(object):
    def evaluate(self, u, v):
        raise Exception("not implemented!")

    def evaluate_array(self, us, vs):
        raise Exception("not implemented!")

    def normal(self, u, v):
        raise Exception("not implemented!")

    def normal_array(self, us, vs):
        raise Exception("not implemented!")

    def get_coord_mode(self):
        return 'UV'

    @property
    def has_input_matrix(self):
        return False

    def get_input_matrix(self):
        return None

    def get_input_orientation(self):
        return None

    def get_u_min(self):
        return 0.0

    def get_u_max(self):
        return 1.0

    def get_v_min(self):
        return 0.0

    def get_v_max(self):
        return 1.0

class SvExRbfSurface(SvExSurface):
    def __init__(self, rbf, coord_mode, input_orientation, input_matrix):
        self.rbf = rbf
        self.coord_mode = coord_mode
        self.input_orientation = input_orientation
        self.input_matrix = input_matrix
        self.u_bounds = (0, 0)
        self.v_bounds = (0, 0)
        self.normal_delta = 0.0001

    def get_input_orientation(self):
        return self.input_orientation

    def get_coord_mode(self):
        return self.coord_mode

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    @property
    def has_input_matrix(self):
        return self.coord_mode == 'XY' and self.input_matrix is not None and self.input_matrix != Matrix()

    def get_input_matrix(self):
        return self.input_matrix

    def evaluate(self, u, v):
        z = self.rbf(u, v)
        if self.coord_mode == 'XY':
            z = np.array([u, v, z])
        return z

    def evaluate_array(self, us, vs):
        surf_vertices = np.array( self.rbf(us, vs) )
        if self.coord_mode == 'XY':
            surf_vertices = np.dstack((us, vs, surf_vertices))[0]
        return surf_vertices 

    def normal(self, u, v):
        return self.normal_array(np.array([u]), np.array([v]))[0]

    def normal_array(self, us, vs):
        surf_vertices = self.evaluate_array(us, vs)
        u_plus = self.evaluate_array(us + self.normal_delta, vs)
        v_plus = self.evaluate_array(us, vs + self.normal_delta)
        du = u_plus - surf_vertices
        dv = v_plus - surf_vertices
        #self.info("Du: %s", du)
        #self.info("Dv: %s", dv)
        normal = np.cross(du, dv)
        norm = np.linalg.norm(normal, axis=1)[np.newaxis].T
        #if norm != 0:
        normal = normal / norm
        #self.info("Normals: %s", normal)
        return normal

class SvExGeomdlSurface(SvExSurface):
    def __init__(self, surface):
        self.surface = surface
        self.u_bounds = (0, 1)
        self.v_bounds = (0, 1)

    def get_input_orientation(self):
        return 'Z'

    def get_coord_mode(self):
        return 'UV'

    def get_u_min(self):
        return self.u_bounds[0]

    def get_u_max(self):
        return self.u_bounds[1]

    def get_v_min(self):
        return self.v_bounds[0]

    def get_v_max(self):
        return self.v_bounds[1]

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    @property
    def has_input_matrix(self):
        return False

    def evaluate(self, u, v):
        v = self.surface.evaluate_single((u, v))
        return np.array(v)

    def evaluate_array(self, us, vs):
        uv_coords = list(zip(list(us), list(vs)))
        verts = self.surface.evaluate_list(uv_coords)
        verts = np.array(verts)
        return verts

    def normal(self, u, v):
        return self.normal_array(np.array([u]), np.array([v]))[0]

    def normal_array(self, us, vs):
        if geomdl is not None:
            uv_coords = list(zip(list(us), list(vs)))
            spline_normals = np.array( operations.normal(self.surface, uv_coords) )[:,1,:]
            return spline_normals

class SvExInterpolatingSurface(SvExSurface):
    def __init__(self, u_bounds, v_bounds, u_spline_constructor, v_splines):
        self.v_splines = v_splines
        self.u_spline_constructor = u_spline_constructor
        self.u_bounds = u_bounds
        self.v_bounds = v_bounds

        # Caches
        # v -> Spline
        self._u_splines = {}
        # (u,v) -> vertex
        self._eval_cache = {}
        # (u,v) -> normal
        self._normal_cache = {}

    def get_u_spline(self, v, vertices):
        """Get a spline along U direction for specified value of V coordinate"""
        spline = self._u_splines.get(v, None)
        if spline is not None:
            return spline
        else:
            spline = self.u_spline_constructor(vertices)
            self._u_splines[v] = spline
            return spline

    def _evaluate(self, u, v):
        spline_vertices = [spline.evaluate(v) for spline in self.v_splines]
        u_spline = self.get_u_spline(v, spline_vertices)
        result = u_spline.evaluate(u)
        return result

    def evaluate(self, u, v):
        result = self._eval_cache.get((u,v), None)
        if result is not None:
            return result
        else:
            result = self._evaluate(u, v)
            self._eval_cache[(u,v)] = result
            return result

    def evaluate_array(self, us, vs):
        # FIXME: To be optimized!
        normals = [self._evaluate(u, v) for u,v in zip(us, vs)]
        return np.array(normals)

#     def evaluate_array(self, us, vs):
#         result = np.empty((len(us), 3))
#         v_to_u = defaultdict(list)
#         v_to_i = defaultdict(list)
#         for i, (u, v) in enumerate(zip(us, vs)):
#             v_to_u[v].append(u)
#             v_to_i[v].append(i)
#         for v, us_by_v in v_to_u.items():
#             is_by_v = v_to_i[v]
#             spline_vertices = [spline.evaluate(v) for spline in self.v_splines]
#             u_spline = self.get_u_spline(v, spline_vertices)
#             points = u_spline.evaluate_array(np.array(us_by_v))
#             np.put(result, is_by_v, points)
#         return result

    def _normal(self, u, v):
        h = 0.001
        point = self.evaluate(u, v)
        # we know this exists because it was filled in evaluate()
        u_spline = self._u_splines[v]
        u_tangent = u_spline.tangent(u)
        point_v = self.evaluate(u, v+h)
        dv = (point_v - point)/h
        n = np.cross(u_tangent, dv)
        norm = np.linalg.norm(n)
        if norm != 0:
            n = n / norm
        return n

    def normal(self, u, v):
        result = self._normal_cache.get((u,v), None)
        if result is not None:
            return result
        else:
            result = self._normal(u, v)
            self._normal_cache[(u,v)] = result
            return result

    def normal_array(self, us, vs):
        # FIXME: To be optimized!
        normals = [self._normal(u, v) for u,v in zip(us, vs)]
        return np.array(normals)

class SvExDeformedByFieldSurface(SvExSurface):
    def __init__(self, surface, field, coefficient=1.0):
        self.surface = surface
        self.field = field
        self.coefficient = coefficient
        self.normal_delta = 0.001

    def get_coord_mode(self):
        return self.surface.get_coord_mode()

    def get_u_min(self):
        return self.surface.get_u_min()

    def get_u_max(self):
        return self.surface.get_u_max()

    def get_v_min(self):
        return self.surface.get_v_min()

    def get_v_max(self):
        return self.surface.get_v_max()

    @property
    def u_size(self):
        return self.surface.u_size

    @property
    def v_size(self):
        return self.surface.v_size

    @property
    def has_input_matrix(self):
        return self.surface.has_input_matrix

    def get_input_matrix(self):
        return self.surface.get_input_matrix()

    def evaluate(self, u, v):
        p = self.surface.evaluate(u, v)
        vec = self.field.evaluate(p)
        return p + self.coefficient * vec

    def evaluate_array(self, us, vs):
        ps = self.surface.evaluate_array(us, vs)
        xs, ys, zs = ps[:,0], ps[:,1], ps[:,2]
        vxs, vys, vzs = self.field.evaluate_grid(xs, ys, zs)
        vecs = np.stack((vxs, vys, vzs)).T
        return ps + self.coefficient * vecs

    def normal(self, u, v):
        h = self.normal_delta
        p = self.evaluate(u, v)
        p_u = self.evaluate(u+h, v)
        p_v = self.evaluate(u, v+h)
        du = (p_u - p) / h
        dv = (p_v - p) / h
        normal = np.cross(du, dv)
        n = np.linalg.norm(normal)
        normal = normal / n
        return normal

    def normal_array(self, us, vs):
        surf_vertices = self.evaluate_array(us, vs)
        u_plus = self.evaluate_array(us + self.normal_delta, vs)
        v_plus = self.evaluate_array(us, vs + self.normal_delta)
        du = u_plus - surf_vertices
        dv = v_plus - surf_vertices
        #self.info("Du: %s", du)
        #self.info("Dv: %s", dv)
        normal = np.cross(du, dv)
        norm = np.linalg.norm(normal, axis=1)[np.newaxis].T
        #if norm != 0:
        normal = normal / norm
        #self.info("Normals: %s", normal)
        return normal

def register():
    pass

def unregister():
    pass

