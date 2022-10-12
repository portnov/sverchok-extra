
bl_info = {
    "name": "Sverchok-Extra",
    "author": "Ilya Portnov",
    "version": (0, 1, 0, 0),
    "blender": (2, 81, 0),
    "location": "Node Editor",
    "category": "Node",
    "description": "Sverchok Extra",
    "warning": "",
    "wiki_url": "http://nikitron.cc.ua/sverch/html/main.html",
    "tracker_url": "http://www.blenderartists.org/forum/showthread.php?272679"
}

import sys
import importlib

import nodeitems_utils

from sverchok.core import make_node_list
from sverchok.utils import auto_gather_node_classes
from sverchok.utils.logging import info, debug
from sverchok.ui.nodeview_space_menu import add_node_menu

# make sverchok the root module name, (if sverchok dir not named exactly "sverchok")
if __name__ != "sverchok_extra":
    sys.modules["sverchok_extra"] = sys.modules[__name__]

from sverchok_extra import icons
from sverchok_extra import settings
from sverchok_extra.utils import show_welcome

def nodes_index():
    return [("Extra Surfaces", [
                ("surface.smooth_spline", "SvExBivariateSplineNode"),
                ("surface.curvature_lines", "SvExSurfaceCurvatureLinesNode"),
                ("surface.implicit_surface_solver", "SvExImplSurfaceSolverNode"),
                ("surface.triangular_mesh", "SvExGalGenerateMeshNode")
            ]),
            ("Extra Curves", [
                ("curve.intersect_surface_plane", "SvExCrossSurfacePlaneNode"),
                ("curve.fourier_curve", "SvFourierCurveNode"),
                ("curve.approximate_fourier_curve", "SvApproxFourierCurveNode"),
                ("curve.interpolate_fourier_curve", "SvInterpFourierCurveNode"),
                ("curve.geodesic_curve", "SvExGeodesicCurveNode"),
                None,
                ("curve.nurbs_goal_point", "SvNurbsCurvePointsGoalNode"),
                ("curve.nurbs_goal_tangent", "SvNurbsCurveTangentsGoalNode"),
                ("curve.nurbs_goal_closed", "SvNurbsCurveClosedGoalNode"),
                ("curve.nurbs_goal_cpt", "SvNurbsCurveCptGoalNode"),
                ("curve.nurbs_solver", "SvNurbsCurveSolverNode")
            ]),
            ("Extra Fields", [
                ("field.vfield_lines_on_surface", "SvExVFieldLinesOnSurfNode"),
                ('sdf.estimate_bounds', "SvExSdfEstimateBoundsNode")
            ]),
            ("Extra Solids", [
                ("solid.solid_waffle", "SvSolidWaffleNode")
            ]),
            ("Extra Spatial", [
                ("spatial.delaunay3d_surface", "SvDelaunayOnSurfaceNode"),
                ("spatial.delaunay_mesh", "SvDelaunayOnMeshNode")
            ]),
            ("Extra Matrix", [
                ('matrix.project_matrix', "SvProjectMatrixNode"),
            ]),
            ('SDF Primitives', [
                ("sdf_primitives.sdf_sphere", "SvExSdfSphereNode"),
                ("sdf_primitives.sdf_box", "SvExSdfBoxNode"),
                ("sdf_primitives.sdf_platonic_solid", "SvExSdfPlatonicSolidNode"),
                ("sdf_primitives.sdf_plane", "SvExSdfPlaneNode"),
                ("sdf_primitives.sdf_slab", "SvExSdfSlabNode"),
                ("sdf_primitives.sdf_rounded_box", "SvExSdfRoundedBoxNode"),
                ("sdf_primitives.sdf_torus", "SvExSdfTorusNode"),
                ("sdf_primitives.sdf_cylinder", "SvExSdfCylinderNode"),
                ("sdf_primitives.sdf_rounded_cylinder", "SvExSdfRoundedCylinderNode"),
                ("sdf_primitives.sdf_capsule", "SvExSdfCapsuleNode"),
                None,
                ("sdf_primitives.sdf2d_circle", "SvExSdf2dCircleNode"),
                ("sdf_primitives.sdf2d_hexagon", "SvExSdf2dHexagonNode"),
                ("sdf_primitives.sdf2d_polygon", "SvExSdf2dPolygonNode"),
            ]),
            ('SDF Operations', [
                ('sdf.sdf_translate', 'SvExSdfTranslateNode'),
                ('sdf.sdf_scale', 'SvExSdfScaleNode'),
                ('sdf.sdf_rotate', 'SvExSdfRotateNode'),
                ('sdf.sdf_orient', 'SvExSdfOrientNode'),
                ('sdf.sdf_transform', 'SvExSdfTransformNode'),
                None,
                ('sdf.sdf_boolean', 'SvExSdfBooleanNode'),
                ('sdf.sdf_blend', 'SvExSdfBlendNode'),
                ('sdf.sdf_transition_linear', 'SvExSdfLinearTransitionNode'),
                ('sdf.sdf_transition_radial', 'SvExSdfRadialTransitionNode'),
                ('sdf.sdf_dilate_erode', 'SvExSdfDilateErodeNode'),
                ('sdf.sdf_shell', 'SvExSdfShellNode'),
                ('sdf.sdf_twist', 'SvExSdfTwistNode'),
                ('sdf.sdf_linear_bend', 'SvExSdfLinearBendNode'),
                None,
                ('sdf.sdf_slice', 'SvExSdfSliceNode'),
                ('sdf.sdf_extrude', 'SvExSdfExtrudeNode'),
                ('sdf.sdf_extrude_to', 'SvExSdfExtrudeToNode'),
                ('sdf.sdf_revolve', 'SvExSdfRevolveNode'),
                None,
                ('sdf.sdf_generate', 'SvExSdfGenerateNode'),
            ]),
            ("Data", [
                ("data.spreadsheet", "SvSpreadsheetNode"),
                ("data.data_item", "SvDataItemNode")
            ])
    ]


def convert_config(config):
    new_form = []
    for cat_name, items in config:
        new_items = []
        for item in items:
            if item is None:
                new_items.append('---')
                continue
            path, bl_idname = item
            new_items.append(bl_idname)
        cat = {cat_name: new_items}
        new_form.append(cat)
    return new_form


add_node_menu.append_from_config(convert_config(nodes_index()))


def make_node_list():
    modules = []
    base_name = "sverchok_extra.nodes"
    index = nodes_index()
    for category, items in index:
        for item in items:
            if not item:
                continue
            module_name, node_name = item
            module = importlib.import_module(f".{module_name}", base_name)
            modules.append(module)
    return modules

imported_modules = [icons] + make_node_list()

reload_event = False

if "bpy" in locals():
    reload_event = True
    info("Reloading sverchok-extra...")

import bpy

def register_nodes():
    node_modules = make_node_list()
    for module in node_modules:
        module.register()
    info("Registered %s nodes", len(node_modules))

def unregister_nodes():
    global imported_modules
    for module in reversed(imported_modules):
        module.unregister()


our_menu_classes = []

def reload_modules():
    global imported_modules
    for im in imported_modules:
        debug("Reloading: %s", im)
        importlib.reload(im)

def register():
    global our_menu_classes

    debug("Registering sverchok-extra")

    add_node_menu.register()
    settings.register()
    icons.register()

    register_nodes()
    extra_nodes = importlib.import_module(".nodes", "sverchok_extra")
    auto_gather_node_classes(extra_nodes)
    show_welcome()

def unregister():
    global our_menu_classes
    if 'SVERCHOK_EXTRA' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK_EXTRA")
    for clazz in our_menu_classes:
        try:
            bpy.utils.unregister_class(clazz)
        except Exception as e:
            print("Can't unregister menu class %s" % clazz)
            print(e)
    unregister_nodes()

    icons.unregister()
    settings.unregister()
