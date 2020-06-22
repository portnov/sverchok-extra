
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
        first_install = self.package in dependencies and dependencies[self.package] is None
        cmd = [PYPATH, '-m', 'pip', 'install', '--upgrade'] + self.package.split(" ")
        ok = subprocess.call(cmd) == 0
        if ok:
            if first_install:
                self.report({'INFO'}, "%s installed successfully. Please restart Blender to see effect." % self.package)
            else:
                self.report({'INFO'}, "%s upgraded successfully. Please restart Blender to see effect." % self.package)
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
class SvExSetFreeCadPath(bpy.types.Operator):
    """Save FreeCAD path in system"""
    bl_idname = "node.sv_ex_set_freecad_path"
    bl_label = "Set FreeCAD path"
    bl_options = {'REGISTER', 'INTERNAL'}
    FreeCAD_folder: bpy.props.StringProperty(name="FreeCAD python 3.7 folder")
    def execute(self, context):
        import sys
        import os
        site_packages = ''
        for p in sys.path:
            if 'site-packages' in p:
                site_packages = p
                break

        file_path= open(os.path.join(site_packages, "freecad_path.pth"), "w+")
        file_path.write(self.FreeCAD_folder)
        file_path.close()
        self.report({'INFO'}, "FreeCad path saved successfully. Please restart Blender to see effect.")
        return {'FINISHED'}


class SvExPreferences(AddonPreferences):
    bl_idname = __package__

    FreeCAD_folder: bpy.props.StringProperty(name="FreeCAD python 3.7 folder")
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
            elif dependency.pip_installable and pip is not None:
                op = row.operator('node.sv_ex_pip_install', text="Upgrade with PIP").package = dependency.package
            return row
        def draw_freeCad_ops(package):
            dependency = dependencies[package]
            col = box.column(align=True)
            col.label(text=dependency.message, icon=get_icon(dependency.module))
            row = col.row(align=True)
            row.operator('wm.url_open', text="Visit package website").url = dependency.url
            if dependency.module is None:
                row.prop(self, 'FreeCAD_folder')
                row.operator('node.sv_ex_set_freecad_path', text="Set path").FreeCAD_folder= self.FreeCAD_folder
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
        draw_freeCad_ops("freecad")


        if any(package.module is None for package in dependencies.values()):
            box.operator('wm.url_open', text="Read installation instructions for missing dependencies").url = "https://github.com/portnov/sverchok-extra"

def register():
    bpy.utils.register_class(SvExPipInstall)
    bpy.utils.register_class(SvExEnsurePip)
    bpy.utils.register_class(SvExSetFreeCadPath)
    bpy.utils.register_class(SvExPreferences)


def unregister():
    bpy.utils.unregister_class(SvExPreferences)
    bpy.utils.unregister_class(SvExEnsurePip)
    bpy.utils.unregister_class(SvExSetFreeCadPath)
    bpy.utils.unregister_class(SvExPipInstall)

if __name__ == '__main__':
    register()
