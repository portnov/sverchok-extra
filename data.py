
import numpy as np
from mathutils import Matrix
from mathutils import noise

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
#         def get_values(field, xs, ys, zs):
#             vx, vy, vz = field.evaluate_grid(xs, ys, zs)
#             vectors = np.transpose( np.stack((vx, vy, vz)), axes=(1,2,3,0))
#             return vectors
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


def register():
    pass

def unregister():
    pass
