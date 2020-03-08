
import numpy as np
from math import sqrt, atanh, sinh, cosh

from sverchok_extra.dependencies import scipy
from sverchok_extra.data.curve import SvExCurve
from scipy.optimize import root_scalar

class CatenaryFormula(SvExCurve):
    def __init__(self, A, x0, point1, force, x_direction, x_range):
        self.A = A
        self.x0 = x0
        self.point1 = point1
        self.force = force
        self.x_direction = x_direction
        self.x_range = x_range
        self.tangent_delta = 0.001

    def eval_y(self, x):
        return self.A * cosh((x - self.x0) / self.A)

    def evaluate(self, t):
        dx = t * self.x_direction[np.newaxis].T
        y = self.A * np.cosh((t - self.x0) / self.A)
        y1 = self.A * np.cosh((- self.x0) / self.A)
        dy = - (y-y1) * self.force[np.newaxis].T
        return self.point1 + dx + dy

    def evaluate_array(self, ts):
        dxs = ts * self.x_direction[np.newaxis].T
        ys = self.A * np.cosh((ts - self.x0) / self.A)
        y1 = self.A * np.cosh((- self.x0) / self.A)
        dys = - (ys - y1) * self.force[np.newaxis].T
        return self.point1 + (dxs + dys).T

    def tangent(self, t):
        point = self.evaluate(t)
        point_h = self.function(t+self.tangent_delta)
        return (point_h - point) / self.tangent_delta

    def tangent_array(self, ts):
        points = self.evaluate_array(ts)
        points_h = self.evaluate_array(ts + self.tangent_delta)
        return (points_h - points) / self.tangent_delta
    
    def get_u_bounds(self):
        return (0.0, self.x_range)

class CatenarySolver(object):
    # Equations:
    # Catenary curve:
    #
    # y = A * cosh( (x-x0) / A) + B  (*)
    #
    # Here we are searching for A, B and x0, so that
    # the curve goes through the point1 and point2, and
    # the segment of the curve between them equals to `length`.
    #
    # We have to project everything onto a plane, so that:
    # * point1, point2, and force vector all lie in that plane;
    # * Y axis of that plane is opposite to the force direction.
    # The origin of the plane can be chosen arbitrary.
    # Let's assume that point1 has coordinates of (0, 0) in that plane.
    # Than point2 will have coordinates of (dx, dy).
    #
    # It can be shown that 
    # * B has no matter at all;
    # * A and x0 can be found from equations
    #
    #  2 * A * sinh( dx / (2*A) ) = sqrt( L^2 - dy^2 )  (1)
    #
    #  (x3 - x0) / A = arctanh( dy / L )                (2)
    #
    # where x3 = dx / 2.
    #
    # The (1) equation can not be solved algebraically; we have to solve it
    # numerically. For any numeric algorithm, we have to provide at least
    # an initial guess and / or a range where to find the solution.
    #
    # By writing the left-hand side of (1) as Taylor series, and taking first three
    # summands only, one can show that some approximation of the solution for (1)
    # can be provided by the following formula:
    #
    #                   5 * dx + sqrt( 5 * dx * (6 * S - dx) )
    # 4 * A^2 = dx^2 * ----------------------------------------    (3)
    #                          60 * (S - dx)
    #
    # We will use (3) as an initial guess, and search for initial range (A0 - dA; A0 + dA).
    #
    def __init__(self, point1, point2, length, force):
        self.point1 = point1
        self.point2 = point2
        self.length = length
        self.force = force / np.linalg.norm(force)
        self._init()

    def _init(self):
        dv = self.point2 - self.point1
        force_direction = self.force
        self.dy = - dv.dot(force_direction)
        dx_v = dv + self.dy * force_direction
        self.dx = np.linalg.norm(dx_v)
        self.x_direction = dx_v / self.dx
        if self.dx < 0:
            self.dx = -self.dx
            self.dy = -self.dy
            self.point1, self.point2 = self.point2, self.point1
            self.x_direction = - self.x_direction
        # Right-hand side of the (1) equation
        self.S = sqrt(self.length * self.length - self.dy * self.dy)

    def _goal(self, A):
        # Left-hand side of (1) equation
        return 2 * A * sinh (self.dx / (2*A))

    def _init_guess(self):
        d = self.dx
        S = self.S
        x2 = d*d * (5*d + sqrt(5*d * (6*S - d))) / (60 * (S - d))
        return sqrt(x2) / 2

    def _bracket(self, A0):
        dA = 0.1
        S = self.S
        coeff = 2.0
        counter = 0
        while True:
            y1 = self._goal(A0 - dA) - S
            y2 = self._goal(A0 + dA) - S
            if y1 * y2 < 0:
                return (A0 - dA), (A0 + dA)
            dA = dA * coeff
            counter += 1
            if counter > 10:
                raise Exception("Can't find initial range")

    def solve(self):
        # Solve (1) equation
        A0 = self._init_guess()
        left, right = self._bracket(A0)
        S = self.S
        result = root_scalar(lambda A: self._goal(A) - S, method='ridder', bracket=(left, right), x0=A0)
        A = result.root

        # Solve (2) equation
        x3 = self.dx / 2.0
        x0 = x3 - A * atanh(self.dy / self.length)
        
        return CatenaryFormula(A, x0, self.point1, self.force, self.x_direction, self.dx)
