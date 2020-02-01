
import numpy as np

from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.logging import info, debug, error, exception
from sverchok.utils.modules.eval_formula import get_variables, sv_compile, safe_eval_compiled

from sverchok_extra.data.field.scalar import *

def make_scalar_field(formula):
    in_field = None
    compiled = sv_compile(formula)
    def function(x, y, z, V):
        variables = dict(x=x, y=y, z=z, V=V)
        return safe_eval_compiled(compiled, variables)
    field = SvExScalarFieldLambda(function, None, in_field)
    return field

class ConstScalarFieldTestCase(SverchokTestCase):
    def test_const_single(self):
        field = SvExConstantScalarField(0.5)
        value = field.evaluate(1, 2, 3)
        expected = 0.5
        self.assert_sverchok_data_equal(value, expected)

    def test_const_grid(self):
        field = SvExConstantScalarField(0.5)
        xs = np.array([[[1, 2]]])
        ys = np.array([[[2, 3]]])
        zs = np.array([[[3, 4]]])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([[[0.5, 0.5]]])
        self.assert_numpy_arrays_equal(r, expected)

class ScalarFieldMathTestCase(SverchokTestCase):
    def test_scalar_field_lambda(self):
        field = make_scalar_field("x*x + y*y + z*z")
        value = field.evaluate(1, 2, 3)
        expected = 14
        self.assert_sverchok_data_equal(value, expected)

    def test_scalar_field_plus(self):
        field1 = make_scalar_field("x+y+z")
        field2 = make_scalar_field("x*y*z")
        field = SvExScalarFieldBinOp(field1, field2, lambda x,y: x+y)
        xs = np.array([[[1, 2]]])
        ys = np.array([[[2, 3]]])
        zs = np.array([[[3, 4]]])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([[[12, 33]]])
        self.assert_numpy_arrays_equal(r, expected)

    def test_scalar_field_negate(self):
        field1 = make_scalar_field("x+y+z")
        field = SvExNegatedScalarField(field1)
        xs = np.array([[[1, 2]]])
        ys = np.array([[[2, 3]]])
        zs = np.array([[[3, 4]]])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([[[-6, -9]]])
        self.assert_numpy_arrays_equal(r, expected)

class KdtScalarFieldTestCase(SverchokTestCase):
    def test_kdt_scalar_field(self):
        vertices = [[1, 2, 3], [10, 10, 10]]
        field = SvExKdtScalarField(vertices=vertices)
        xs = np.array([[[1, 2]]])
        ys = np.array([[[2, 3]]])
        zs = np.array([[[3, 4]]])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([[[0, 1.732]]])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

class LineAttractorTestCase(SverchokTestCase):
    def test_line_attractor(self):
        center = np.array((0, 0, 0))
        direction = np.array((1, 0, 0))
        field = SvExLineAttractorScalarField(center, direction)

        xs = np.array([[[1, 2]]])
        ys = np.array([[[2, 3]]])
        zs = np.array([[[3, 4]]])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([[[3.606, 5]]])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

class PlaneAttractorTestCase(SverchokTestCase):
    def test_plane_attractor(self):
        center = np.array((0, 0, 0))
        direction = np.array((1, 0, 0))
        field = SvExPlaneAttractorScalarField(center, direction)

        xs = np.array([[[1, 2]]])
        ys = np.array([[[2, 3]]])
        zs = np.array([[[3, 4]]])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([[[1, 2]]])
        self.assert_numpy_arrays_equal(r, expected, precision=3)
