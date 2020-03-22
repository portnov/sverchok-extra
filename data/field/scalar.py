
from sverchok.utils.field.scalar import SvExScalarField

##################
#                #
#  Scalar Fields #
#                #
##################

class SvExRbfScalarField(SvExScalarField):
    def __init__(self, rbf):
        self.rbf = rbf

    def evaluate(self, x, y, z):
        return self.rbf(x, y, z)

    def evaluate_grid(self, xs, ys, zs):
        value = self.rbf(xs, ys, zs)
        return value

def register():
    pass

def unregister():
    pass

