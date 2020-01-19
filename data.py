
import numpy as np
from mathutils import Matrix, Vector
from mathutils import noise
from mathutils import kdtree
from mathutils import bvhtree

coordinate_modes = [
    ('XYZ', "Carthesian", "Carthesian coordinates - x, y, z", 0),
    ('CYL', "Cylindrical", "Cylindrical coordinates - rho, phi, z", 1),
    ('SPH', "Spherical", "Spherical coordinates - rho, phi, theta", 2)
]

##################
#                #
#  Surfaces      #
#                #
##################

class SvExRbfSurface(object):
    def __init__(self, rbf, coord_mode, input_orientation, input_matrix):
        self.rbf = rbf
        self.coord_mode = coord_mode
        self.input_orientation = input_orientation
        self.input_matrix = input_matrix
        self.u_bounds = (0, 0)
        self.v_bounds = (0, 0)

    @property
    def u_size(self):
        return self.u_bounds[1] - self.u_bounds[0]

    @property
    def v_size(self):
        return self.v_bounds[1] - self.v_bounds[0]

    @property
    def has_matrix(self):
        return self.coord_mode == 'XY' and self.input_matrix is not None and self.input_matrix != Matrix()

##################
#                #
#  Scalar Fields #
#                #
##################

class SvExScalarField(object):
    def evaluate(self, point):
        raise Exception("not implemented")

    def evaluate_grid(self, xs, ys, zs):
        raise Exception("not implemented")

class SvExConstantScalarField(SvExScalarField):
    def __init__(self, value):
        self.value = value

    def evaluate(self, x, y, z):
        return self.value

    def evaluate_grid(self, xs, ys, zs):
        result = np.full_like(xs, self.value)
        return result

class SvExScalarFieldLambda(SvExScalarField):
    def __init__(self, function, variables, in_field):
        self.function = function
        self.variables = variables
        self.in_field = in_field

    def evaluate_grid(self, xs, ys, zs):
        if self.in_field is None:
            Vs = np.zeros((xs.shape[0], ys.shape[0], zs.shape[0]))
        else:
            Vs = self.in_field.evaluate_grid(xs, ys, zs)
        return np.vectorize(self.function)(xs, ys, zs, Vs)

    def evaluate(self, x, y, z):
        if self.in_field is None:
            V = None
        else:
            V = self.in_field.evaluate(x, y, z)
        return self.function(x, y, z, V)

class SvExScalarFieldPointDistance(SvExScalarField):
    def __init__(self, center, falloff=None):
        self.center = center
        self.falloff = falloff

    def evaluate_grid(self, xs, ys, zs):
        x0, y0, z0 = tuple(self.center)
        xs = xs - x0
        ys = ys - y0
        zs = zs - z0
        points = np.stack((xs, ys, zs))
        norms = np.linalg.norm(points, axis=0)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

    def evaluate(self, x, y, z):
        return np.linalg.norm( np.array([x, y, z]) - self.center)

class SvExScalarFieldBinOp(SvExScalarField):
    def __init__(self, field1, field2, function):
        self.function = function
        self.field1 = field1
        self.field2 = field2

    def evaluate(self, x, y, z):
        return self.function(self.field1.evaluate(x, y, z), self.field2.evaluate(x, y, z))

    def evaluate_grid(self, xs, ys, zs):
        func = lambda xs, ys, zs : self.function(self.field1.evaluate_grid(xs, ys, zs), self.field2.evaluate_grid(xs, ys, zs))
        return np.vectorize(func, signature="(m,n,p),(m,n,p),(m,n,p)->(m,n,p)")(xs, ys, zs)

class SvExNegatedScalarField(SvExScalarField):
    def __init__(self, field):
        self.field = field

    def evaluate(self, x, y, z):
        v = self.field.evaluate(x, y, z)
        return -x

    def evaluate_grid(self, xs, ys, zs):
        def func(xs, ys, zs):
            return - self.field.evaluate_grid(xs, ys, zs)
        return np.vectorize(func, signature="(m,n,p),(m,n,p),(m,n,p)->(m,n,p)")(xs, ys, zs)

class SvExVectorFieldsScalarProduct(SvExScalarField):
    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x, y, z)
        v2 = self.field2.evaluate(x, y, z)
        return np.dot(v1, v2)

    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.transpose( np.stack((vx1, vy1, vz1)), axes=(1,2,3,0))
        vectors2 = np.transpose( np.stack((vx2, vy2, vz2)), axes=(1,2,3,0))
        result = np.vectorize(np.dot, signature="(3),(3)->()")(vectors1, vectors2)
        return result

class SvExVectorFieldNorm(SvExScalarField):
    def __init__(self, field):
        self.field = field

    def evaluate(self, x, y, z):
        v = self.field.evaluate(x, y, z)
        return np.norm(v)

    def evaluate_grid(self, xs, ys, zs):
        vx, vy, vz = self.field.evaluate_grid(xs, ys, zs)
        vectors = np.transpose( np.stack((vx, vy, vz)), axes=(1,2,3,0))
        result = np.vectorize(np.linalg.norm, signature="(3)->()")(vectors)
        return result

class SvExMergedScalarField(SvExScalarField):
    def __init__(self, mode, fields):
        self.mode = mode
        self.fields = fields

    def evaluate(self, x, y, z):
        values = np.array([field.evaluate(x, y, z) for field in self.fields])
        if self.mode == 'MIN':
            value = np.min(values)
        elif self.mode == 'MAX':
            value = np.max(values)
        elif self.mode == 'SUM':
            value = np.sum(values)
        elif self.mode == 'AVG':
            value = np.mean(values)
        else:
            raise Exception("unsupported operation")
        return value

    def evaluate_grid(self, xs, ys, zs):
        values = np.array([field.evaluate_grid(xs, ys, zs) for field in self.fields])
        if self.mode == 'MIN':
            value = np.min(values, axis=0)
        elif self.mode == 'MAX':
            value = np.max(values, axis=0)
        elif self.mode == 'SUM':
            value = np.sum(values, axis=0)
        elif self.mode == 'AVG':
            value = np.mean(values, axis=0)
        else:
            raise Exception("unsupported operation")
        return value

class SvExKdtScalarField(SvExScalarField):
    def __init__(self, vertices=None, kdt=None, falloff=None):
        self.falloff = falloff
        if kdt is not None:
            self.kdt = kdt
        elif vertices is not None:
            self.kdt = kdtree.KDTree(len(vertices))
            for i, v in enumerate(vertices):
                self.kdt.insert(v, i)
            self.kdt.balance()
        else:
            raise Exception("Either kdt or vertices must be provided")

    def evaluate(self, x, y, z):
        nearest, i, distance = self.kdt.find((x, y, z))
        if self.falloff is not None:
            value = self.falloff(np.array([distance]))[0]
            return value
        else:
            return distance

    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, i, distance = self.kdt.find(v)
            return distance

        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        norms = np.vectorize(find, signature='(3)->()')(points)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

class SvExLineAttractorScalarField(SvExScalarField):
    def __init__(self, center, direction, falloff=None):
        self.center = center
        self.direction = direction
        self.falloff = falloff

    def evaluate(self, x, y, z):
        vertex = np.array([x,y,z])
        direction = self.direction
        to_center = self.center - vertex
        projection = np.dot(to_center, direction) * direction / np.dot(direction, direction)
        dv = to_center - projection
        return np.linalg.norm(dv)

    def evaluate_grid(self, xs, ys, zs):
        direction = self.direction
        direction2 = np.dot(direction, direction)

        def func(vertex):
            to_center = self.center - vertex
            projection = np.dot(to_center, direction) * direction / direction2
            dv = to_center - projection
            return np.linalg.norm(dv)

        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        norms = np.vectorize(func, signature='(3)->()')(points)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

class SvExPlaneAttractorScalarField(SvExScalarField):
    def __init__(self, center, direction, falloff=None):
        self.center = center
        self.direction = direction
        self.falloff = falloff

    def evaluate(self, x, y, z):
        vertex = np.array([x,y,z])
        direction = self.direction
        to_center = self.center - vertex
        projection = np.dot(to_center, direction) * direction / np.dot(direction, direction)
        return np.linalg.norm(projection)

    def evaluate_grid(self, xs, ys, zs):
        direction = self.direction
        direction2 = np.dot(direction, direction)

        def func(vertex):
            to_center = self.center - vertex
            projection = np.dot(to_center, direction) * direction / direction2
            return np.linalg.norm(projection)

        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        norms = np.vectorize(func, signature='(3)->()')(points)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

class SvExBvhAttractorScalarField(SvExScalarField):
    def __init__(self, bvh=None, verts=None, faces=None, falloff=None):
        self.falloff = falloff
        if bvh is not None:
            self.bvh = bvh
        elif verts is not None and faces is not None:
            self.bvh = bvhtree.BVHTree.FromPolygons(verts, faces)
        else:
            raise Exception("Either bvh or verts and faces must be provided!")

    def evaluate(self, x, y, z):
        nearest, normal, idx, distance = self.bvh.find_nearest((x,y,z))
        return distance

    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, normal, idx, distance = self.bvh.find_nearest(v)
            if nearest is None:
                raise Exception("No nearest point on mesh found for vertex %s" % v)
            return distance

        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        norms = np.vectorize(find, signature='(3)->()')(points)
        if self.falloff is not None:
            result = self.falloff(norms)
            return result
        else:
            return norms

##################
#                #
#  Vector Fields #
#                #
##################

class SvExVectorField(object):
    def evaluate(self, point):
        raise Exception("not implemented")

    def evaluate_grid(self, xs, ys, zs):
        raise Exception("not implemented")

class SvExMatrixVectorField(SvExVectorField):
    def __init__(self, matrix):
        self.matrix = matrix

    def evaluate(self, x, y, z):
        v = self.matrix @ Vector((x,y,z))
        return np.array(v)

    def evaluate_grid(self, xs, ys, zs):
        matrix = np.array(self.matrix.to_3x3())
        translation = np.array(self.matrix.translation)
        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        R = np.apply_along_axis(lambda v : matrix @ v + translation, 3, points)
        return R[:,:,:,0], R[:,:,:,1], R[:,:,:,2]

class SvExVectorFieldLambda(SvExVectorField):
    def __init__(self, function, variables, in_field):
        self.function = function
        self.variables = variables
        self.in_field = in_field

    def evaluate_grid(self, xs, ys, zs):
        if self.in_field is None:
            Vs = np.zeros((xs.shape[0], ys.shape[0], zs.shape[0]))
        else:
            Vs = self.in_field.evaluate_grid(xs, ys, zs)
        return np.vectorize(self.function,
                    signature = "(),(),(),()->(),(),()")(xs, ys, zs, Vs)

    def evaluate(self, x, y, z):
        if self.in_field is None:
            V = None
        else:
            V = self.in_field.evaluate(x, y, z)
        return self.function(x, y, z, V)

class SvExVectorFieldBinOp(SvExVectorField):
    def __init__(self, field1, field2, function):
        self.function = function
        self.field1 = field1
        self.field2 = field2

    def evaluate(self, x, y, z):
        return self.function(self.field1.evaluate(x, y, z), self.field2.evaluate(x, y, z))

    def evaluate_grid(self, xs, ys, zs):
        func = lambda xs, ys, zs : self.function(self.field1.evaluate_grid(xs, ys, zs), self.field2.evaluate_grid(xs, ys, zs))
        return np.vectorize(func, signature="(m,n,p),(m,n,p),(m,n,p)->(m,n,p),(m,n,p),(m,n,p)")(xs, ys, zs)

class SvExAverageVectorField(SvExVectorField):
    def __init__(self, fields):
        self.fields = fields

    def evaluate(self, x, y, z):
        vectors = np.array([field.evaluate(x, y, z) for field in self.fields])
        return np.mean(vectors, axis=0)

    def evaluate_grid(self, xs, ys, zs):
        def func(xs, ys, zs):
            data = []
            for field in self.fields:
                vx, vy, vz = field.evaluate_grid(xs, ys, zs)
                vectors = np.transpose( np.stack((vx, vy, vz)), axes=(1,2,3,0))
                data.append(vectors)
            data = np.array(data)
            mean = np.mean(data, axis=0)
            return mean[:,:,:,0],mean[:,:,:,1],mean[:,:,:,2]
        return np.vectorize(func, signature="(m,n,p),(m,n,p),(m,n,p)->(m,n,p),(m,n,p),(m,n,p)")(xs, ys, zs)

class SvExVectorFieldCrossProduct(SvExVectorField):
    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x, y, z)
        v2 = self.field1.evaluate(x, y, z)
        return np.cross(v1, v2)

    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.transpose( np.stack((vx1, vy1, vz1)), axes=(1,2,3,0))
        vectors2 = np.transpose( np.stack((vx2, vy2, vz2)), axes=(1,2,3,0))
        def cross(v1, v2):
            v = np.cross(v1, v2)
            return v[0], v[1], v[2]
        return np.vectorize(cross, signature="(3),(3)->(),(),()")(vectors1, vectors2)

class SvExVectorFieldMultipliedByScalar(SvExVectorField):
    def __init__(self, vector_field, scalar_field):
        self.vector_field = vector_field
        self.scalar_field = scalar_field

    def evaluate(self, x, y, z):
        scalar = self.scalar_field.evaluate(x, y, z)
        vector = self.vector_field.evaluate(x, y, z)
        return scalar * vector

    def evaluate_grid(self, xs, ys, zs):
        def product(xs, ys, zs):
            scalars = self.scalar_field.evaluate_grid(xs, ys, zs)
            vx, vy, vz = self.vector_field.evaluate_grid(xs, ys, zs)
            vectors = np.vstack((vx, vy, vz))
            R = scalars * vectors
            return R[0,:,:][np.newaxis], R[1,:,:][np.newaxis], R[2,:,:][np.newaxis]
        return np.vectorize(product, signature="(m,n,p),(m,n,p),(m,n,p)->(m,n,p),(m,n,p),(m,n,p)")(xs, ys, zs)

class SvExRbfVectorField(SvExVectorField):
    def __init__(self, rbf):
        self.rbf = rbf

    def evaluate(self, x, y, z):
        return self.rbf(x, y, z) - np.array([x, y, z])

    def evaluate_grid(self, xs, ys, zs):
        value = self.rbf(xs, ys, zs)
        vx = value[:,:,:,0]
        vy = value[:,:,:,1]
        vz = value[:,:,:,2]
        vx = vx - xs
        vy = vy - ys
        vz = vz - zs
        return vx, vy, vz

class SvExNoiseVectorField(SvExVectorField):
    def __init__(self, noise_type, seed):
        self.noise_type = noise_type
        self.seed = seed

    def evaluate(self, x, y, z):
        noise.seed_set(self.seed)
        return noise.noise_vector((x, y, z), noise_basis=self.noise_type)

    def evaluate_grid(self, xs, ys, zs):
        noise.seed_set(self.seed)
        def mk_noise(v):
            r = noise.noise_vector(v, noise_basis=self.noise_type)
            return r[0], r[1], r[2]
        vectors = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        return np.vectorize(mk_noise, signature="(3)->(),(),()")(vectors)

class SvExKdtVectorField(SvExVectorField):
    def __init__(self, vertices=None, kdt=None, falloff=None, negate=False):
        self.falloff = falloff
        self.negate = negate
        if kdt is not None:
            self.kdt = kdt
        elif vertices is not None:
            self.kdt = kdtree.KDTree(len(vertices))
            for i, v in enumerate(vertices):
                self.kdt.insert(v, i)
            self.kdt.balance()
        else:
            raise Exception("Either kdt or vertices must be provided")

    def evaluate(self, x, y, z):
        nearest, i, distance = self.kdt.find((x, y, z))
        vector = np.array(nearest) - np.array([x, y, z])
        if self.falloff is not None:
            value = self.falloff(np.array([distance]))[0]
            if self.negate:
                value = - value
            norm = np.linalg.norm(vector)
            return value * vector / norm
        else:
            if self.negate:
                return - vector
            else:
                return vector

    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, i, distance = self.kdt.find(v)
            dx, dy, dz = np.array(nearest) - np.array(v)
            if self.negate:
                return (-dx, -dy, -dz)
            else:
                return (dx, dy, dz)

        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        vectors = np.vectorize(find, signature='(3)->(),(),()')(points)
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=0)
            lens = self.falloff(norms)
            R = lens * vectors
            return R[0,:,:], R[1,:,:], R[2,:,:]
        else:
            return vectors

class SvExVectorFieldPointDistance(SvExVectorField):
    def __init__(self, center, falloff=None):
        self.center = center
        self.falloff = falloff

    def evaluate_grid(self, xs, ys, zs):
        x0, y0, z0 = tuple(self.center)
        xs = x0 - xs
        ys = y0 - ys
        zs = z0 - zs
        vectors = np.stack((xs, ys, zs))
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=0)
            lens = self.falloff(norms)
            R = lens * vectors
            return R[0,:,:], R[1,:,:], R[2,:,:]
        else:
            R = vectors
            return R[0,:,:], R[1,:,:], R[2,:,:]

    def evaluate(self, x, y, z):
        vector = np.array([x, y, z]) - self.center
        if self.fallof is not None:
            norm = np.norm(vector)
            value = self.falloff(np.array([distance]))[0]
            return value * vector / norm
        else:
            return vector

class SvExLineAttractorVectorField(SvExVectorField):
    def __init__(self, center, direction, falloff=None):
        self.center = center
        self.direction = direction
        self.falloff = falloff

    def evaluate(self, x, y, z):
        vertex = np.array([x,y,z])
        direction = self.direction
        to_center = self.center - vertex
        projection = np.dot(to_center, direction) * direction / np.dot(direction, direction)
        dv = to_center - projection
        return dv

    def evaluate_grid(self, xs, ys, zs):
        direction = self.direction
        direction2 = np.dot(direction, direction)

        def func(vertex):
            to_center = self.center - vertex
            projection = np.dot(to_center, direction) * direction / direction2
            dv = to_center - projection
            return dv

        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        vectors = np.vectorize(func, signature='(3)->(3)')(points)
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=0)
            lens = self.falloff(norms)
            R = lens * vectors
            return R[:,:,:,0], R[:,:,:,1], R[:,:,:,2]
        else:
            R = vectors
            return R[:,:,:,0], R[:,:,:,1], R[:,:,:,2]

class SvExPlaneAttractorVectorField(SvExVectorField):
    def __init__(self, center, direction, falloff=None):
        self.center = center
        self.direction = direction
        self.falloff = falloff

    def evaluate(self, x, y, z):
        vertex = np.array([x,y,z])
        direction = self.direction
        to_center = self.center - vertex
        projection = np.dot(to_center, direction) * direction / np.dot(direction, direction)
        return projection

    def evaluate_grid(self, xs, ys, zs):
        direction = self.direction
        direction2 = np.dot(direction, direction)

        def func(vertex):
            to_center = self.center - vertex
            projection = np.dot(to_center, direction) * direction / direction2
            return projection

        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        vectors = np.vectorize(func, signature='(3)->(3)')(points)
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=0)
            lens = self.falloff(norms)
            R = lens * vectors
            return R[:,:,:,0], R[:,:,:,1], R[:,:,:,2]
        else:
            R = vectors
            return R[:,:,:,0], R[:,:,:,1], R[:,:,:,2]

class SvExBvhAttractorVectorField(SvExVectorField):
    def __init__(self, bvh=None, verts=None, faces=None, falloff=None, use_normal=False):
        self.falloff = falloff
        self.use_normal = use_normal
        if bvh is not None:
            self.bvh = bvh
        elif verts is not None and faces is not None:
            self.bvh = bvhtree.BVHTree.FromPolygons(verts, faces)
        else:
            raise Exception("Either bvh or verts and faces must be provided!")

    def evaluate(self, x, y, z):
        vertex = Vector((x,y,z))
        nearest, normal, idx, distance = self.bvh.find_nearest(vertex)
        if self.use_normal:
            return np.array(normal)
        else:
            return np.array(nearest - vertex)

    def evaluate_grid(self, xs, ys, zs):
        def find(v):
            nearest, normal, idx, distance = self.bvh.find_nearest(v)
            if nearest is None:
                raise Exception("No nearest point on mesh found for vertex %s" % v)
            if self.use_normal:
                return np.array(normal)
            else:
                return np.array(nearest) - v

        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        vectors = np.vectorize(find, signature='(3)->(3)')(points)
        if self.falloff is not None:
            norms = np.linalg.norm(vectors, axis=0)
            lens = self.falloff(norms)
            R = lens * vectors
            return R[:,:,:,0], R[:,:,:,1], R[:,:,:,2]
        else:
            R = vectors
            return R[:,:,:,0], R[:,:,:,1], R[:,:,:,2]

class SvExVectorFieldTangent(SvExVectorField):
    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x,y,z)
        v2 = self.field2.evaluate(x,y,z)
        projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
        return projection
    
    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.transpose( np.stack((vx1, vy1, vz1)), axes=(1,2,3,0))
        vectors2 = np.transpose( np.stack((vx2, vy2, vz2)), axes=(1,2,3,0))

        def project(v1, v2):
            projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
            vx, vy, vz = projection
            return vx, vy, vz

        return np.vectorize(project, signature="(3),(3)->(),(),()")(vectors1, vectors2)

class SvExVectorFieldCotangent(SvExVectorField):
    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2

    def evaluate(self, x, y, z):
        v1 = self.field1.evaluate(x,y,z)
        v2 = self.field2.evaluate(x,y,z)
        projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
        return v1 - projection
    
    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.transpose( np.stack((vx1, vy1, vz1)), axes=(1,2,3,0))
        vectors2 = np.transpose( np.stack((vx2, vy2, vz2)), axes=(1,2,3,0))

        def project(v1, v2):
            projection = np.dot(v1, v2) * v2 / np.dot(v2, v2)
            coprojection = v1 - projection
            vx, vy, vz = coprojection
            return vx, vy, vz

        return np.vectorize(project, signature="(3),(3)->(),(),()")(vectors1, vectors2)

class SvExVectorFieldComposition(SvExVectorField):
    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2

    def evaluate(self, x, y, z):
        x1, y1, z1 = self.field1.evaluate(x,y,z)
        v2 = self.field2.evaluate(x1,y1,z1)
        return v2
    
    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        return self.field2.evaluate_grid(vx1, vy1, vz1)

def register():
    pass

def unregister():
    pass
