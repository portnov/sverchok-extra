
import sys
import subprocess

import bpy
from bpy.types import AddonPreferences

if bpy.app.version >= (2, 91, 0):
    PYPATH = sys.executable
else:
    PYPATH = bpy.app.binary_path_python

from sverchok.dependencies import draw_message
from sverchok_extra.dependencies import ex_dependencies, pip, ensurepip

class SvExPreferences(AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout

        def get_icon(package):
            if package is None:
                return 'CANCEL'
            else:
                return 'CHECKMARK'

        box = layout.box()

        box.label(text="Dependencies:")
        draw_message(box, "sverchok", dependencies=ex_dependencies)
        draw_message(box, "pygalmesh", dependencies=ex_dependencies)
        draw_message(box, "sdf", dependencies=ex_dependencies)
        draw_message(box, "scipy")
        draw_message(box, "pyexcel", dependencies=ex_dependencies)
        draw_message(box, "pyexcel_xls", dependencies=ex_dependencies)
        draw_message(box, "pyexcel_xlsx", dependencies=ex_dependencies)
        draw_message(box, "pyexcel_ods", dependencies=ex_dependencies)
        draw_message(box, "pyexcel_io", dependencies=ex_dependencies)
        draw_message(box, "awkward", dependencies=ex_dependencies)


def register():
    bpy.utils.register_class(SvExPreferences)


def unregister():
    bpy.utils.unregister_class(SvExPreferences)

if __name__ == '__main__':
    register()
