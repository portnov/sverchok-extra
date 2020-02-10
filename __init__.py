
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
from sverchok.menu import SverchNodeItem, node_add_operators, SverchNodeCategory, register_node_panels, unregister_node_panels, unregister_node_add_operators
from sverchok.utils.extra_categories import register_extra_category_provider
from sverchok.ui.nodeview_space_menu import make_extra_category_menus
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.logging import info, debug

# make sverchok the root module name, (if sverchok dir not named exactly "sverchok") 
if __name__ != "sverchok_extra":
    sys.modules["sverchok_extra"] = sys.modules[__name__]

from sverchok_extra import sockets
from sverchok_extra import data
from sverchok_extra import icons
from sverchok_extra import settings
from sverchok_extra.utils import show_welcome

def nodes_index():
    return [("Surface", [
                ("surface.plane", "SvExPlaneSurfaceNode"),
                ("surface.minimal_surface", "SvExMinimalSurfaceNode"),
                ("surface.smooth_spline", "SvExBivariateSplineNode"),
                ("surface.nurbs_surface", "SvExNurbsSurfaceNode"),
                ("surface.interpolate_nurbs_surface", "SvExInterpolateNurbsSurfaceNode"),
                ("surface.approximate_nurbs_surface", "SvExApproxNurbsSurfaceNode"),
                ("surface.interpolating_surface", "SvExInterpolatingSurfaceNode"),
                ("surface.quads_to_nurbs", "SvExQuadsToNurbsNode"),
                ("surface.marching_cubes", "SvExMarchingCubesNode"),
                ("surface.apply_field_to_surface", "SvExApplyFieldToSurfaceNode"),
                ("surface.evaluate_surface", "SvExEvalSurfaceNode")
            ]),
            ("Curve", [
                ("curve.line", "SvExLineCurveNode"),
                ("curve.curve_formula", "SvExCurveFormulaNode"),
                ("curve.interpolation_curve", "SvExSplineCurveNode"),
                ("curve.rbf_curve", "SvExRbfCurveNode"),
                ("curve.nurbs_curve", "SvExNurbsCurveNode"),
                ("curve.interpolate_nurbs_curve", "SvExInterpolateNurbsCurveNode"),
                ("curve.approximate_nurbs_curve", "SvExApproxNurbsCurveNode"),
                ("curve.apply_field_to_curve", "SvExApplyFieldToCurveNode"),
                ("curve.eval_curve", "SvExEvalCurveNode"),
                ("curve.marching_squares", "SvExMarchingSquaresNode")
            ]),
            ("Field", [
                ("field.scalar_field_formula", "SvExScalarFieldFormulaNode"),
                ("field.vector_field_formula", "SvExVectorFieldFormulaNode"),
                ("field.compose_vector_field", "SvExComposeVectorFieldNode"),
                ("field.decompose_vector_field", "SvExDecomposeVectorFieldNode"),
                ("field.scalar_field_point", "SvExScalarFieldPointNode"),
                ("field.attractor_field", "SvExAttractorFieldNode"),
                ("field.mesh_normal_field", "SvExMeshNormalFieldNode"),
                ("field.scalar_field_math", "SvExScalarFieldMathNode"),
                ("field.merge_scalar_fields", "SvExMergeScalarFieldsNode"),
                ("field.scalar_field_eval", "SvExScalarFieldEvaluateNode"),
                ("field.minimal_vfield", "SvExMinimalVectorFieldNode"),
                ("field.minimal_sfield", "SvExMinimalScalarFieldNode"),
                ("field.vector_field_eval", "SvExVectorFieldEvaluateNode"),
                ("field.vector_field_apply", "SvExVectorFieldApplyNode"),
                ("field.vector_field_math", "SvExVectorFieldMathNode"),
                ("field.noise_vfield", "SvExNoiseVectorFieldNode"),
                ("field.curve_bend_field", "SvExBendAlongCurveFieldNode"),
                ("field.bend_along_surface", "SvExBendAlongSurfaceFieldNode"),
                ("field.differential_operations", "SvExFieldDiffOpsNode")
            ]),
            ("Spatial", [
                ("spatial.voronoi3d", "SvExVoronoi3DNode"),
                ("spatial.voronoi_sphere", "SvExVoronoiSphereNode"),
                ("spatial.field_random_probe", "SvExFieldRandomProbeNode")
            ])
    ]

def make_node_list():
    modules = []
    base_name = "sverchok_extra.nodes"
    index = nodes_index()
    for category, items in index:
        for module_name, node_name in items:
            module = importlib.import_module(f".{module_name}", base_name)
            modules.append(module)
    return modules

imported_modules = [sockets, data, icons] + make_node_list()

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
        identifier = "SVERCHOK_EXTRA_" + category
        node_items = []
        for item in items:
            nodetype = item[1]
            rna = get_node_class_reference(nodetype)
            if not rna:
                info("Node `%s' is not available (probably due to missing dependencies).", nodetype)
            else:
                node_item = SverchNodeItem.new(nodetype) 
                node_items.append(node_item)

        cat = SverchNodeCategory(
                    identifier,
                    category,
                    items = node_items
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
    debug("Registering sverchok-extra")
    global our_menu_classes

    settings.register()
    sockets.register()
    data.register()
    icons.register()

    register_nodes()
    extra_nodes = importlib.import_module(".nodes", "sverchok_extra")
    auto_gather_node_classes(extra_nodes)    
    menu = make_menu()
    provider = SvExCategoryProvider("SVERCHOK_EXTRA", menu)
    register_extra_category_provider(provider)
    #if 'SVERCHOK_EXTRA' in nodeitems_utils._node_categories:
        #unregister_node_panels()
        #nodeitems_utils.unregister_node_categories("SVERCHOK_EXTRA")
    nodeitems_utils.register_node_categories("SVERCHOK_EXTRA", menu)
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
    #unregister_node_add_operators()
    unregister_nodes()

    icons.unregister()
    data.unregister()
    sockets.unregister()
    settings.unregister()

