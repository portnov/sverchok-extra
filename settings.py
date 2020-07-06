
import subprocess

import bpy
from bpy.types import AddonPreferences

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

def register():
    bpy.utils.register_class(SvExPreferences)


def unregister():
    bpy.utils.unregister_class(SvExPreferences)

if __name__ == '__main__':
    register()
