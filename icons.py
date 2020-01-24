
import os
import glob

from sverchok.ui.sv_icons import register_custom_icon_provider

class SvExIconProvider(object):
    def __init__(self):
        pass

    def get_icons(self):
        icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        icon_pattern = "sv_ex_*.png"
        icon_path = os.path.join(icons_dir, icon_pattern)
        icon_files = [os.path.basename(x) for x in glob.glob(icon_path)]

        for icon_file in icon_files:
            icon_name = os.path.splitext(icon_file)[0]
            icon_id = icon_name.upper()
            yield icon_id, os.path.join(icons_dir, icon_file)

def register():
    register_custom_icon_provider("sverchok_extra", SvExIconProvider())

def unregister():
    pass

