
from mathutils import Matrix

class SvExRbfSurface(object):
    def __init__(self, rbf, coord_mode, input_orientation, input_matrix):
        self.rbf = rbf
        self.coord_mode = coord_mode
        self.input_orientation = input_orientation
        self.input_matrix = input_matrix

    @property
    def has_matrix(self):
        return self.coord_mode == 'XY' and self.input_matrix is not None and self.input_matrix != Matrix()

def register():
    pass

def unregister():
    pass
