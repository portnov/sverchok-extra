
import numpy as np

from sverchok.utils.modules.eval_formula import get_variables, sv_compile, safe_eval_compiled

from sverchok_extra.data.field.scalar import SvExScalarFieldLambda
from sverchok_extra.data.field.vector import SvExVectorFieldLambda

def make_vector_field(formula1, formula2, formula3):
    in_field = None
    compiled1 = sv_compile(formula1)
    compiled2 = sv_compile(formula2)
    compiled3 = sv_compile(formula3)
    def function(x, y, z, V):
        variables = dict(x=x, y=y, z=z, V=V)
        v1 = safe_eval_compiled(compiled1, variables)
        v2 = safe_eval_compiled(compiled2, variables)
        v3 = safe_eval_compiled(compiled3, variables)
        return v1, v2, v3
    field = SvExVectorFieldLambda(function, None, in_field)
    return field

def make_scalar_field(formula):
    in_field = None
    compiled = sv_compile(formula)
    def function(x, y, z, V):
        variables = dict(x=x, y=y, z=z, V=V)
        return safe_eval_compiled(compiled, variables)
    field = SvExScalarFieldLambda(function, None, in_field)
    return field

