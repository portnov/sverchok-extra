
from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.field.scalar import *

from sverchok_extra.data.field.scalar import *
from sverchok_extra.tests.make_fields import make_vector_field
from sverchok_extra.tests.make_fields import make_scalar_field


class ConstScalarFieldTestCase(SverchokTestCase):
    def test_const_single(self):
        field = SvExConstantScalarField(0.5)
        value = field.evaluate(1, 2, 3)
        expected = 0.5
        self.assert_sverchok_data_equal(value, expected)

    def test_const_grid(self):
        field = SvExConstantScalarField(0.5)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([0.5, 0.5])
        self.assert_numpy_arrays_equal(r, expected)

class DecomposeFieldTestCase(SverchokTestCase):
    def test_x(self):
        field1 = make_vector_field("2*x", "3*y", "4*z")
        field = SvExVectorFieldDecomposed(field1, 'XYZ', 0)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([2, 4])
        self.assert_numpy_arrays_equal(r, expected)

    def test_y(self):
        field1 = make_vector_field("2*x", "3*y", "4*z")
        field = SvExVectorFieldDecomposed(field1, 'XYZ', 1)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([6, 9])
        self.assert_numpy_arrays_equal(r, expected)

    def test_z(self):
        field1 = make_vector_field("2*x", "3*y", "4*z")
        field = SvExVectorFieldDecomposed(field1, 'XYZ', 2)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([12, 16])
        self.assert_numpy_arrays_equal(r, expected)

    def test_cyl_rho(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExVectorFieldDecomposed(field1, 'CYL', 0)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([2.236, 3.606])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_cyl_phi(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExVectorFieldDecomposed(field1, 'CYL', 1)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([1.107, 0.983])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_cyl_z(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExVectorFieldDecomposed(field1, 'CYL', 2)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([3, 4])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_sph_rho(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExVectorFieldDecomposed(field1, 'SPH', 0)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([3.742, 5.385])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_cyl_phi(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExVectorFieldDecomposed(field1, 'SPH', 1)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([1.107, 0.983])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_cyl_z(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExVectorFieldDecomposed(field1, 'SPH', 2)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([0.641, 0.734])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

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
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([12, 33])
        self.assert_numpy_arrays_equal(r, expected)

    def test_scalar_field_negate(self):
        field1 = make_scalar_field("x+y+z")
        field = SvExNegatedScalarField(field1)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([-6, -9])
        self.assert_numpy_arrays_equal(r, expected)

    def test_scalar_product(self):
        field1 = make_vector_field("x", "y", "z")
        field2 = make_vector_field("-y", "x", "z")
        field = SvExVectorFieldsScalarProduct(field1, field2)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([9, 16])
        self.assert_numpy_arrays_equal(r, expected)

    def test_norm(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExVectorFieldNorm(field1)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([3.742, 5.385])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

class AttractorTestCase(SverchokTestCase):
    def test_kdt_scalar_field(self):
        vertices = [[1, 2, 3], [10, 10, 10]]
        field = SvExKdtScalarField(vertices=vertices)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([0, 1.732])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_line_attractor(self):
        center = np.array((0, 0, 0))
        direction = np.array((1, 0, 0))
        field = SvExLineAttractorScalarField(center, direction)

        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([3.606, 5])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_plane_attractor(self):
        center = np.array((0, 0, 0))
        direction = np.array((1, 0, 0))
        field = SvExPlaneAttractorScalarField(center, direction)

        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([1, 2])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_distance(self):
        center = np.array([0, 0, 0])
        field = SvExScalarFieldPointDistance(center)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([3.742, 5.385])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_bvh(self):
        verts = [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]
        faces = [[0, 1, 2, 3]]
        field = SvExBvhAttractorScalarField(verts=verts, faces=faces)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])

        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([2.449, 4.123])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

class ScalarFieldDiffOpsTestCase(SverchokTestCase):
    def test_divergence(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExVectorFieldDivergence(field1, 0.0001)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([3, 3])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

    def test_laplacian(self):
        field1 = make_scalar_field("x+y+z")
        field = SvExScalarFieldLaplacian(field1, 0.0001)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        r = field.evaluate_grid(xs, ys, zs)
        expected = np.array([0, 0])
        self.assert_numpy_arrays_equal(r, expected, precision=3)

