
import numpy as np
import os

from sverchok.utils.math import inverse, inverse_square, inverse_cubic

rbf_functions = [
    ('multiquadric', "Multi Quadric", "Multi Quadric", 0),
    ('inverse', "Inverse", "Inverse", 1),
    ('gaussian', "Gaussian", "Gaussian", 2),
    ('cubic', "Cubic", "Cubic", 3),
    ('quintic', "Quintic", "Qunitic", 4),
    ('thin_plate', "Thin Plate", "Thin Plate", 5)
]

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

