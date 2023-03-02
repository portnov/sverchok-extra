
from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.field.scalar import *
from sverchok.utils.field.vector import *

from sverchok_extra.data.field.scalar import *
from sverchok_extra.data.field.vector import *
from sverchok_extra.tests.make_fields import make_vector_field
from sverchok_extra.tests.make_fields import make_scalar_field


class MatrixVectorFieldTestCase(SverchokTestCase):
    def test_matrix(self):
        matrix = Matrix.Scale(2, 4)
        field = SvExMatrixVectorField(matrix)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])

        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([1, 2])
        expected_y = np.array([2, 3])
        expected_z = np.array([3, 4])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

class ConstVectorFieldTestCase(SverchokTestCase):
    def test_constant(self):
        v = np.array([1, 2, 3])
        field = SvExConstantVectorField(v)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([1, 1])
        expected_y = np.array([2, 2])
        expected_z = np.array([3, 3])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

class ComposeVectorFieldTestCase(SverchokTestCase):
    def test_xyz(self):
        field1 = make_scalar_field("x")
        field2 = make_scalar_field("y")
        field3 = make_scalar_field("z")
        field = SvExComposedVectorField('XYZ', field1, field2, field3)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([1, 2])
        expected_y = np.array([2, 3])
        expected_z = np.array([3, 4])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_cyl_const(self):
        field1 = SvExConstantScalarField(1)
        field2 = SvExConstantScalarField(0.5)
        field3 = SvExConstantScalarField(0.7)
        field = SvExComposedVectorField('CYL', field1, field2, field3)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0.878, 0.878])
        expected_y = np.array([0.479, 0.479])
        expected_z = np.array([0.7, 0.7])
        self.assert_numpy_arrays_equal(rxs, expected_x, precision=3)
        self.assert_numpy_arrays_equal(rys, expected_y, precision=3)
        self.assert_numpy_arrays_equal(rzs, expected_z, precision=3)

    def test_sph_const(self):
        field1 = SvExConstantScalarField(1)
        field2 = SvExConstantScalarField(0.5)
        field3 = SvExConstantScalarField(0.7)
        field = SvExComposedVectorField('SPH', field1, field2, field3)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0.565, 0.565])
        expected_y = np.array([0.309, 0.309])
        expected_z = np.array([0.765, 0.765])
        self.assert_numpy_arrays_equal(rxs, expected_x, precision=3)
        self.assert_numpy_arrays_equal(rys, expected_y, precision=3)
        self.assert_numpy_arrays_equal(rzs, expected_z, precision=3)

class AbsoluteVectorFieldTestCase(SverchokTestCase):
    def test_abs(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExAbsoluteVectorField(field1)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([2, 4])
        expected_y = np.array([4, 6])
        expected_z = np.array([6, 8])
        self.assert_numpy_arrays_equal(rxs, expected_x, precision=3)
        self.assert_numpy_arrays_equal(rys, expected_y, precision=3)
        self.assert_numpy_arrays_equal(rzs, expected_z, precision=3)

class RelativeVectorFieldTestCase(SverchokTestCase):
    def test_abs(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExRelativeVectorField(field1)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, 0])
        expected_y = np.array([0, 0])
        expected_z = np.array([0, 0])
        self.assert_numpy_arrays_equal(rxs, expected_x, precision=3)
        self.assert_numpy_arrays_equal(rys, expected_y, precision=3)
        self.assert_numpy_arrays_equal(rzs, expected_z, precision=3)

class LambdaVectorFieldTestCase(SverchokTestCase):
    def test_lambda(self):
        field = make_vector_field("-y", "x", "z")
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([-2, -3])
        expected_y = np.array([1, 2])
        expected_z = np.array([3, 4])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

class VectorFieldMathTestCase(SverchokTestCase):
    def test_cross_product(self):
        field1 = make_vector_field("-y", "x", "z")
        field2 = make_vector_field("-y", "x", "z")
        field = SvExVectorFieldCrossProduct(field1, field2)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, 0])
        expected_y = np.array([0, 0])
        expected_z = np.array([0, 0])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_lerp(self):
        field1 = make_vector_field("-x", "y", "z")
        field2 = make_vector_field("x", "-y", "z")
        scalar = SvExConstantScalarField(0.5)
        field = SvExVectorFieldsLerp(field1, field2, scalar)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, 0])
        expected_y = np.array([0, 0])
        expected_z = np.array([3, 4])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_average(self):
        field1 = make_vector_field("x", "y", "z")
        field2 = make_vector_field("-x", "-y", "-z")
        field = SvExAverageVectorField([field1, field2])
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, 0])
        expected_y = np.array([0, 0])
        expected_z = np.array([0, 0])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_multiply_by_scalar(self):
        field1 = make_vector_field("x", "y", "z")
        scalar = SvExConstantScalarField(2)
        field = SvExVectorFieldMultipliedByScalar(field1, scalar)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([2, 4])
        expected_y = np.array([4, 6])
        expected_z = np.array([6, 8])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

class AttractorVectorFieldTestCase(SverchokTestCase):
    def test_point(self):
        center = np.array([0, 0, 0])
        field = SvExVectorFieldPointDistance(center)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([-1, -2])
        expected_y = np.array([-2, -3])
        expected_z = np.array([-3, -4])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_line(self):
        center = np.array((0, 0, 0))
        direction = np.array((1, 0, 0))
        field = SvExLineAttractorVectorField(center, direction)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, 0])
        expected_y = np.array([-2, -3])
        expected_z = np.array([-3, -4])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_plane(self):
        center = np.array((0, 0, 0))
        direction = np.array((1, 0, 0))
        field = SvExPlaneAttractorVectorField(center, direction)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([-1, -2])
        expected_y = np.array([0, 0])
        expected_z = np.array([0, 0])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_bvh(self):
        verts = [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]
        faces = [[0, 1, 2, 3]]
        field = SvExBvhAttractorVectorField(verts=verts, faces=faces)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([-1, -2])
        expected_y = np.array([-1, -2])
        expected_z = np.array([-2, -3])
        self.assert_numpy_arrays_equal(rxs, expected_x, precision=3)
        self.assert_numpy_arrays_equal(rys, expected_y, precision=3)
        self.assert_numpy_arrays_equal(rzs, expected_z, precision=3)

class KdtVectorFieldTestCase(SverchokTestCase):
    def test_kdt(self):
        vertices = [[1, 2, 3], [10, 10, 10]]
        field = SvExKdtVectorField(vertices=vertices)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, -1])
        expected_y = np.array([0, -1])
        expected_z = np.array([0, -1])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

class ProjectVectorFieldsTestCase(SverchokTestCase):
    def test_tangent(self):
        v = np.array([1, 0, 0])
        field1 = make_vector_field("x", "y", "z")
        field2 = SvExConstantVectorField(v)
        field = SvExVectorFieldTangent(field1, field2)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([1, 2])
        expected_y = np.array([0, 0])
        expected_z = np.array([0, 0])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_cotangent(self):
        v = np.array([1, 0, 0])
        field1 = make_vector_field("x", "y", "z")
        field2 = SvExConstantVectorField(v)
        field = SvExVectorFieldCotangent(field1, field2)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, 0])
        expected_y = np.array([2, 3])
        expected_z = np.array([3, 4])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

class VectorFieldDiffOpsTestCase(SverchokTestCase):
    def test_gradient_zero(self):
        field1 = SvExConstantScalarField(0.7)
        field = SvExScalarFieldGradient(field1, 0.0001)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, 0])
        expected_y = np.array([0, 0])
        expected_z = np.array([0, 0])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_gradient_one(self):
        field1 = make_scalar_field("x+y+z")
        field = SvExScalarFieldGradient(field1, 0.0001)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([1, 1])
        expected_y = np.array([1, 1])
        expected_z = np.array([1, 1])
        self.assert_numpy_arrays_equal(rxs, expected_x, precision=3)
        self.assert_numpy_arrays_equal(rys, expected_y, precision=3)
        self.assert_numpy_arrays_equal(rzs, expected_z, precision=3)

    def test_rotor_zero(self):
        field1 = make_vector_field("x", "y", "z")
        field = SvExVectorFieldRotor(field1, 0.0001)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, 0])
        expected_y = np.array([0, 0])
        expected_z = np.array([0, 0])
        self.assert_numpy_arrays_equal(rxs, expected_x)
        self.assert_numpy_arrays_equal(rys, expected_y)
        self.assert_numpy_arrays_equal(rzs, expected_z)

    def test_rotor_one(self):
        field1 = make_vector_field("-y", "x", "z")
        field = SvExVectorFieldRotor(field1, 0.0001)
        xs = np.array([1, 2])
        ys = np.array([2, 3])
        zs = np.array([3, 4])
        rxs, rys, rzs = field.evaluate_grid(xs, ys, zs)
        expected_x = np.array([0, 0])
        expected_y = np.array([0, 0])
        expected_z = np.array([2, 2])
        self.assert_numpy_arrays_equal(rxs, expected_x, precision=4)
        self.assert_numpy_arrays_equal(rys, expected_y, precision=4)
        self.assert_numpy_arrays_equal(rzs, expected_z, precision=4)


