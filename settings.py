
import subprocess

import bpy
from bpy.types import AddonPreferences

PYPATH = bpy.app.binary_path_python

from sverchok_extra.dependencies import dependencies, pip, ensurepip

class SvExPipInstall(bpy.types.Operator):
    """Install the package by calling pip install"""
    bl_idname = 'node.sv_ex_pip_install'
    bl_label = "Install the package"
    bl_options = {'REGISTER', 'INTERNAL'}

    package : bpy.props.StringProperty(name = "Package names")

    def execute(self, context):
        cmd = [PYPATH, '-m', 'pip', 'install', '--upgrade'] + self.package.split(" ")
        ok = subprocess.call(cmd) == 0
        if ok:
            self.report({'INFO'}, "%s installed successfully. Please restart Blender to see effect." % self.package)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Cannot install %s, see console output for details" % self.package)
            return {'CANCELLED'}

class SvExEnsurePip(bpy.types.Operator):
    """Install PIP by using ensurepip module"""
    bl_idname = "node.sv_ex_ensurepip"
    bl_label = "Install PIP"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        cmd = [PYPATH, '-m', 'ensurepip']
        ok = subprocess.call(cmd) == 0
        if ok:
            self.report({'INFO'}, "PIP installed successfully. Please restart Blender to see effect.")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Cannot install PIP, see console output for details")
            return {'CANCELLED'}

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

        def draw_message(package):
            dependency = dependencies[package]
            col = box.column(align=True)
            col.label(text=dependency.message, icon=get_icon(dependency.module))
            row = col.row(align=True)
            row.operator('wm.url_open', text="Visit package website").url = dependency.url
            if dependency.module is None and dependency.pip_installable and pip is not None:
                row.operator('node.sv_ex_pip_install', text="Install with PIP").package = dependency.package
            return row

        box.label(text="Dependencies:")
        draw_message("sverchok")
        row = draw_message("pip")
        if pip is not None:
            row.operator('node.sv_ex_pip_install', text="Upgrade PIP").package = "pip setuptools wheel"
        else:
            if ensurepip is not None:
                row.operator('node.sv_ex_ensurepip', text="Install PIP")
            else:
                row.operator('wm.url_open', text="Installation instructions").url = "https://pip.pypa.io/en/stable/installing/"
        draw_message("scipy")
        draw_message("geomdl")
        draw_message("skimage")
        draw_message("mcubes")
        draw_message("circlify")
        draw_message("lbt-ladybug")

        if any(package.module is None for package in dependencies.values()):
            box.operator('wm.url_open', text="Read installation instructions for missing dependencies").url = "https://github.com/portnov/sverchok-extra"

def register():
    bpy.utils.register_class(SvExPipInstall)
    bpy.utils.register_class(SvExEnsurePip)
    bpy.utils.register_class(SvExPreferences)


def unregister():
    bpy.utils.unregister_class(SvExPreferences)
    bpy.utils.unregister_class(SvExEnsurePip)
    bpy.utils.unregister_class(SvExPipInstall)

if __name__ == '__main__':
    register()
