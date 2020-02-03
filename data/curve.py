
import numpy as np
from mathutils import Matrix, Vector
from mathutils import noise
from mathutils import kdtree
from mathutils import bvhtree

##################
#                #
#  Curves        #
#                #
##################

class SvExCurve(object):
    def evaluate(self, t):
        raise Exception("not implemented!")

    def evaluate_array(self, ts):
        raise Exception("not implemented!")

    def tangent(self, t):
        raise Exception("not implemented!")
    
    def tangent_array(self, ts):
        raise Exception("not implemented!")

    def get_u_bounds(self):
        raise Exception("not implemented!")

class SvExGeomdlCurve(SvExCurve):
    def __init__(self, curve):
        self.curve = curve
        self.u_bounds = (0.0, 1.0)

    def evaluate(self, t):
        v = self.curve.evaluate_single(t)
        return np.array(v)

    def evaluate_array(self, ts):
        vs = self.curve.evaluate_list(list(ts))
        return np.array(vs)

    def tangent(self, t):
        v = self.curve.tangent(t)
        return np.array(v)

    def tangent_array(self, ts):
        vs = self.curve.tangent(list(ts))
        return np.array([t[1] for t in vs])

    def get_u_bounds(self):
        return self.u_bounds

class SvExSplineCurve(SvExCurve):
    def __init__(self, spline):
        self.spline = spline

    def evaluate(self, t):
        v = self.spline.eval_at_point(t)
        return np.array(v)

    def evaluate_array(self, ts):
        vs = self.spline.eval(ts)
        return np.array(vs)

    def tangent(self, t):
        vs = self.spline.tangent(np.array([t]))
        return vs[0]

    def tangent_array(self, ts):
        return self.spline.tangent(ts)

    def get_u_bounds(self):
        return (0.0, 1.0)

def register():
    pass

def unregister():
    pass


