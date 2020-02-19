
import numpy as np
import os

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

def show_welcome():
    text = """
   _____                     __          __         ______     __            
  / ___/   _____  __________/ /_  ____  / /__      / ____/  __/ /__________ _
  \__ \ | / / _ \/ ___/ ___/ __ \/ __ \/ //_/_____/ __/ | |/_/ __/ ___/ __ `/
 ___/ / |/ /  __/ /  / /__/ / / / /_/ / ,< /_____/ /____>  </ /_/ /  / /_/ / 
/____/|___/\___/_/   \___/_/ /_/\____/_/|_|     /_____/_/|_|\__/_/   \__,_/
initialized.
"""
    can_paint = os.name in {'posix'}

    with_color = "\033[1;31m{0}\033[0m" if can_paint else "{0}"
    for line in text.splitlines():
        print(with_color.format(line))

