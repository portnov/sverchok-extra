
import numpy as np
from mathutils import Matrix

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

coordinate_modes = [
    ('XYZ', "Carthesian", "Carthesian coordinates - x, y, z", 0),
    ('CYL', "Cylindrical", "Cylindrical coordinates - rho, phi, z", 1),
    ('SPH', "Spherical", "Spherical coordinates - rho, phi, theta", 2)
]

class SvExScalarField(object):
    def evaluate(self, point):
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

def register():
    pass

def unregister():
    pass
