
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
import bl_operators

import sverchok
from sverchok.core import sv_registration_utils, make_node_list
from sverchok.utils import auto_gather_node_classes, get_node_class_reference
from sverchok.menu import SverchNodeItem, SverchSeparator, node_add_operators, SverchNodeCategory, register_node_panels, unregister_node_panels, unregister_node_add_operators
from sverchok.utils.extra_categories import register_extra_category_provider, unregister_extra_category_provider
from sverchok.ui.nodeview_space_menu import make_extra_category_menus
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.logging import info, debug

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
                ("curve.interpolate_fourier_curve", "SvInterpFourierCurveNode")
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
                ("sdf_primitives.sdf_gyroid", "SvExSdfGyroidNode"),
                ("sdf_primitives.sdf_graded_gyroid", "SvExSdfGradedGyroidNode"),
                ("sdf_primitives.sdf_functionally_graded_gyroid", "SvExSdfFunctionallyGradedGyroidNode"),
                ("sdf_primitives.sdf_schwarzP", "SvExSdfSchwarzPNode"),
                ("sdf_primitives.sdf_schwarzD", "SvExSdfSchwarzDNode"),
                ("sdf_primitives.sdf_MO", "SvExSdfMONode"),
                ("sdf_primitives.sdf_EB", "SvExSdfEBNode"),
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
    reload_modules()

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

def make_menu():
    menu = []
    index = nodes_index()
    for category, items in index:
        identifier = "SVERCHOK_EXTRA_" + category.replace(' ', '_')
        node_items = []
        for item in items:
            if not item:
                node_item = SverchSeparator()
                node_items.append(node_item)
                continue

            nodetype = item[1]
            rna = get_node_class_reference(nodetype)
            if not rna:
                info("Node `%s' is not available (probably due to missing dependencies).", nodetype)
            else:
                node_item = SverchNodeItem.new(nodetype)
                node_items.append(node_item)
        if node_items:
            cat = SverchNodeCategory(
                        identifier,
                        category,
                        items=node_items
                    )
            menu.append(cat)
    return menu

class SvExCategoryProvider(object):
    def __init__(self, identifier, menu):
        self.identifier = identifier
        self.menu = menu

    def get_categories(self):
        return self.menu

our_menu_classes = []

def reload_modules():
    global imported_modules
    for im in imported_modules:
        debug("Reloading: %s", im)
        importlib.reload(im)

def register():
    global our_menu_classes

    debug("Registering sverchok-extra")

    settings.register()
    icons.register()

    register_nodes()
    extra_nodes = importlib.import_module(".nodes", "sverchok_extra")
    auto_gather_node_classes(extra_nodes)
    menu = make_menu()
    menu_category_provider = SvExCategoryProvider("SVERCHOK_EXTRA", menu)
    register_extra_category_provider(menu_category_provider) #if 'SVERCHOK_EXTRA' in nodeitems_utils._node_categories:
        #unregister_node_panels()
        #nodeitems_utils.unregister_node_categories("SVERCHOK_EXTRA")

    our_menu_classes = make_extra_category_menus()
    #register_node_panels("SVERCHOK_EXTRA", menu)
    show_welcome()

def unregister():
    global our_menu_classes
    if 'SVERCHOK_EXTRA' in nodeitems_utils._node_categories:
        #unregister_node_panels()
        nodeitems_utils.unregister_node_categories("SVERCHOK_EXTRA")
    for clazz in our_menu_classes:
        try:
            bpy.utils.unregister_class(clazz)
        except Exception as e:
            print("Can't unregister menu class %s" % clazz)
            print(e)
    unregister_extra_category_provider("SVERCHOK_EXTRA")
    #unregister_node_add_operators()
    unregister_nodes()

    icons.unregister()
    settings.unregister()
