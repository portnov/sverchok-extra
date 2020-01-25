
import numpy as np

from sverchok.utils.math import inverse, inverse_square, inverse_cubic

falloff_types = [
        ('NONE', "None - R", "Output distance", 0),
        ("inverse", "Inverse - 1/R", "", 1),
        ("inverse_square", "Inverse square - 1/R^2", "Similar to gravitation or electromagnetizm", 2),
        ("inverse_cubic", "Inverse cubic - 1/R^3", "", 3),
        ("inverse_exp", "Inverse exponent - Exp(-R)", "", 4),
        ("gauss", "Gauss - Exp(-R^2/2)", "", 5)
    ]

rbf_functions = [
    ('multiquadric', "Multi Quadric", "Multi Quadric", 0),
    ('inverse', "Inverse", "Inverse", 1),
    ('gaussian', "Gaussian", "Gaussian", 2),
    ('cubic', "Cubic", "Cubic", 3),
    ('quintic', "Quintic", "Qunitic", 4),
    ('thin_plate', "Thin Plate", "Thin Plate", 5)
]

def inverse_exp(c, x):
    return np.exp(-c*x)

def gauss(c, x):
    return np.exp(-c*x*x/2.0)

def falloff(falloff_type, amplitude, coefficient, clamp=False):
    falloff_func = globals()[falloff_type]

    def function(rho_array):
        zero_idxs = (rho_array == 0)
        nonzero = (rho_array != 0)
        result = np.empty_like(rho_array)
        result[zero_idxs] = amplitude
        result[nonzero] = amplitude * falloff_func(coefficient, rho_array[nonzero])
        negative = result <= 0
        result[negative] = 0.0

        if clamp:
            high = result >= rho_array
            result[high] = rho_array[high]
        return result
    return function

