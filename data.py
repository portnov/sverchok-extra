
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
        return np.linalg.norm(v)

    def evaluate_grid(self, xs, ys, zs):
        vx, vy, vz = self.field.evaluate_grid(xs, ys, zs)
        vectors = np.transpose( np.stack((vx, vy, vz)), axes=(1,2,3,0))
        result = np.linalg.norm(vectors, axis=3)
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

class SvExVectorScalarFieldComposition(SvExScalarField):
    def __init__(self, vfield, sfield):
        self.sfield = sfield
        self.vfield = vfield

    def evaluate(self, x, y, z):
        x1, y1, z1 = self.vfield.evaluate(x,y,z)
        v2 = self.sfield.evaluate(x1,y1,z1)
        return v2
    
    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.vfield.evaluate_grid(xs, ys, zs)
        return self.sfield.evaluate_grid(vx1, vy1, vz1)

class SvExVectorFieldDivergence(SvExScalarField):
    def __init__(self, field, step):
        self.field = field
        self.step = step

    def evaluate(self, x, y, z):
        step = self.step
        xs_dx_plus, _, _ = self.field.evaluate(x+step,y,z)
        xs_dx_minus, _, _ = self.field.evaluate(x-step,y,z)
        _, ys_dy_plus, _ = self.field.evaluate(x, y+step, z)
        _, ys_dy_minus, _ = self.field.evaluate(x, y-step, z)
        _, _, zs_dz_plus = self.field.evaluate(x, y, z+step)
        _, _, zs_dz_minus = self.field.evaluate(x, y, z-step)

        dx_dx = (xs_dx_plus - xs_dx_minus) / (2*step)
        dy_dy = (ys_dy_plus - ys_dy_minus) / (2*step)
        dz_dz = (zs_dz_plus - zs_dz_minus) / (2*step)

        return dx_dx + dy_dy + dz_dz
    
    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        xs_dx_plus, _, _ = self.field.evaluate_grid(xs+step, ys,zs)
        xs_dx_minus, _, _ = self.field.evaluate_grid(xs-step,ys,zs)
        _, ys_dy_plus, _ = self.field.evaluate_grid(xs, ys+step, zs)
        _, ys_dy_minus, _ = self.field.evaluate_grid(xs, ys-step, zs)
        _, _, zs_dz_plus = self.field.evaluate_grid(xs, ys, zs+step)
        _, _, zs_dz_minus = self.field.evaluate_grid(xs, ys, zs-step)

        dx_dx = (xs_dx_plus - xs_dx_minus) / (2*step)
        dy_dy = (ys_dy_plus - ys_dy_minus) / (2*step)
        dz_dz = (zs_dz_plus - zs_dz_minus) / (2*step)

        return dx_dx + dy_dy + dz_dz

class SvExScalarFieldLaplacian(SvExScalarField):
    def __init__(self, field, step):
        self.field = field
        self.step = step

    def evaluate(self, x, y, z):
        step = self.step
        v_dx_plus = self.field.evaluate(x+step,y,z)
        v_dx_minus = self.field.evaluate(x-step,y,z)
        v_dy_plus = self.field.evaluate(x, y+step, z)
        v_dy_minus = self.field.evaluate(x, y-step, z)
        v_dz_plus = self.field.evaluate(x, y, z+step)
        v_dz_minus = self.field.evaluate(x, y, z-step)
        v0 = self.field.evaluate(x, y, z)

        sides = v_dx_plus + v_dx_minus + v_dy_plus + v_dy_minus + v_dz_plus + v_dz_minus
        result = (sides - 6*v0) / (8 * step * step * step)
        return result
    
    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        v_dx_plus = self.field.evaluate_grid(xs+step, ys,zs)
        v_dx_minus = self.field.evaluate_grid(xs-step,ys,zs)
        v_dy_plus = self.field.evaluate_grid(xs, ys+step, zs)
        v_dy_minus = self.field.evaluate_grid(xs, ys-step, zs)
        v_dz_plus = self.field.evaluate_grid(xs, ys, zs+step)
        v_dz_minus = self.field.evaluate_grid(xs, ys, zs-step)
        v0 = self.field.evaluate_grid(xs, ys, zs)

        sides = v_dx_plus + v_dx_minus + v_dy_plus + v_dy_minus + v_dz_plus + v_dz_minus
        result = (sides - 6*v0) / (8 * step * step * step)
        return result

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
        v = Vector((x, y, z))
        v = (self.matrix @ v) - v
        return np.array(v)

    def evaluate_grid(self, xs, ys, zs):
        matrix = np.array(self.matrix.to_3x3())
        translation = np.array(self.matrix.translation)
        points = np.transpose( np.stack((xs, ys, zs)), axes=(1,2,3,0))
        R = np.apply_along_axis(lambda v : matrix @ v + translation - v, 3, points)
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
        def func(xs, ys, zs):
            vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
            vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
            R = self.function(np.array([vx1, vy1, vz1]), np.array([vx2, vy2, vz2]))
            return R[0], R[1], R[2]
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
        v2 = self.field2.evaluate(x, y, z)
        return np.cross(v1, v2)

    def evaluate_grid(self, xs, ys, zs):
        vx1, vy1, vz1 = self.field1.evaluate_grid(xs, ys, zs)
        vx2, vy2, vz2 = self.field2.evaluate_grid(xs, ys, zs)
        vectors1 = np.transpose( np.stack((vx1, vy1, vz1)), axes=(1,2,3,0))
        vectors2 = np.transpose( np.stack((vx2, vy2, vz2)), axes=(1,2,3,0))
        R = np.cross(vectors1, vectors2)
        return R[:,:,:,0], R[:,:,:,1], R[:,:,:,2]
#         def cross(v1, v2):
#             v = np.cross(v1, v2)
#             return v[0], v[1], v[2]
#         return np.vectorize(cross, signature="(3),(3)->(),(),()")(vectors1, vectors2)

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
            vectors = np.stack((vx, vy, vz))
            R = scalars * vectors
            return R[0,:,:], R[1,:,:], R[2,:,:]
        return np.vectorize(product, signature="(m,n,p),(m,n,p),(m,n,p)->(m,n,p),(m,n,p),(m,n,p)")(xs, ys, zs)

class SvExVectorFieldsLerp(SvExVectorField):
    def __init__(self, vfield1, vfield2, scalar_field):
        self.vfield1 = vfield1
        self.vfield2 = vfield2
        self.scalar_field = scalar_field

    def evaluate(self, x, y, z):
        scalar = self.scalar_field.evaluate(x, y, z)
        vector1 = self.vfield1.evaluate(x, y, z)
        vector2 = self.vfield2.evaluate(x, y, z)
        return (1 - scalar) * vector1 + scalar * vector2

    def evaluate_grid(self, xs, ys, zs):
        def product(xs, ys, zs):
            scalars = self.scalar_field.evaluate_grid(xs, ys, zs)
            vx1, vy1, vz1 = self.vfield1.evaluate_grid(xs, ys, zs)
            vectors1 = np.stack((vx1, vy1, vz1))
            vx2, vy2, vz2 = self.vfield2.evaluate_grid(xs, ys, zs)
            vectors2 = np.stack((vx2, vy2, vz2))
            R = (1 - scalars) * vectors1 + scalars * vectors2
            return R[0,:,:], R[1,:,:], R[2,:,:]
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
        if self.falloff is not None:
            norm = np.linalg.norm(vector)
            value = self.falloff(np.array([norm]))[0]
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

class SvExScalarFieldGradient(SvExVectorField):
    def __init__(self, field, step):
        self.field = field
        self.step = step

    def evaluate(self, x, y, z):
        step = self.step
        v_dx_plus = self.field.evaluate(x+step,y,z)
        v_dx_minus = self.field.evaluate(x-step,y,z)
        v_dy_plus = self.field.evaluate(x, y+step, z)
        v_dy_minus = self.field.evaluate(x, y-step, z)
        v_dz_plus = self.field.evaluate(x, y, z+step)
        v_dz_minus = self.field.evaluate(x, y, z-step)

        dv_dx = (v_dx_plus - v_dx_minus) / (2*step)
        dv_dy = (v_dy_plus - v_dy_minus) / (2*step)
        dv_dz = (v_dz_plus - v_dz_minus) / (2*step)
        return np.array([dv_dx, dv_dy, dv_dz])
    
    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        v_dx_plus = self.field.evaluate_grid(xs+step, ys,zs)
        v_dx_minus = self.field.evaluate_grid(xs-step,ys,zs)
        v_dy_plus = self.field.evaluate_grid(xs, ys+step, zs)
        v_dy_minus = self.field.evaluate_grid(xs, ys-step, zs)
        v_dz_plus = self.field.evaluate_grid(xs, ys, zs+step)
        v_dz_minus = self.field.evaluate_grid(xs, ys, zs-step)

        dv_dx = (v_dx_plus - v_dx_minus) / (2*step)
        dv_dy = (v_dy_plus - v_dy_minus) / (2*step)
        dv_dz = (v_dz_plus - v_dz_minus) / (2*step)

        R = np.stack((dv_dx, dv_dy, dv_dz))
        return R[0,:,:], R[1,:,:], R[2,:,:]

class SvExVectorFieldRotor(SvExVectorField):
    def __init__(self, field, step):
        self.field = field
        self.step = step

    def evaluate(self, x, y, z):
        step = self.step
        _, y_dx_plus, z_dx_plus = self.field.evaluate(x+step,y,z)
        _, y_dx_minus, z_dx_minus = self.field.evaluate(x-step,y,z)
        x_dy_plus, _, z_dy_plus = self.field.evaluate(x, y+step, z)
        x_dy_minus, _, z_dy_minus = self.field.evaluate(x, y-step, z)
        x_dz_plus, y_dz_plus, _ = self.field.evaluate(x, y, z+step)
        x_dz_minus, y_dz_minus, _ = self.field.evaluate(x, y, z-step)

        dy_dx = (y_dx_plus - y_dx_minus) / (2*step)
        dz_dx = (z_dx_plus - z_dx_minus) / (2*step)
        dx_dy = (x_dy_plus - x_dy_minus) / (2*step)
        dz_dy = (z_dy_plus - z_dy_minus) / (2*step)
        dx_dz = (x_dz_plus - x_dz_minus) / (2*step)
        dy_dz = (y_dz_plus - y_dz_minus) / (2*step)

        rx = dz_dy - dy_dz
        ry = - (dz_dx - dx_dz)
        rz = dy_dx - dx_dy

        return np.array([rx, ry, rz])

    def evaluate_grid(self, xs, ys, zs):
        step = self.step
        _, y_dx_plus, z_dx_plus = self.field.evaluate_grid(xs+step,ys,zs)
        _, y_dx_minus, z_dx_minus = self.field.evaluate_grid(xs-step,ys,zs)
        x_dy_plus, _, z_dy_plus = self.field.evaluate_grid(xs, ys+step, zs)
        x_dy_minus, _, z_dy_minus = self.field.evaluate_grid(xs, ys-step, zs)
        x_dz_plus, y_dz_plus, _ = self.field.evaluate_grid(xs, ys, zs+step)
        x_dz_minus, y_dz_minus, _ = self.field.evaluate_grid(xs, ys, zs-step)

        dy_dx = (y_dx_plus - y_dx_minus) / (2*step)
        dz_dx = (z_dx_plus - z_dx_minus) / (2*step)
        dx_dy = (x_dy_plus - x_dy_minus) / (2*step)
        dz_dy = (z_dy_plus - z_dy_minus) / (2*step)
        dx_dz = (x_dz_plus - x_dz_minus) / (2*step)
        dy_dz = (y_dz_plus - y_dz_minus) / (2*step)

        rx = dz_dy - dy_dz
        ry = - (dz_dx - dx_dz)
        rz = dy_dx - dx_dy
        R = np.transpose( np.stack((rx, ry, rz)), axes=(1,2,3,0))
        return R[:,:,:,0], R[:,:,:,1], R[:,:,:,2]

def register():
    pass

def unregister():
    pass
