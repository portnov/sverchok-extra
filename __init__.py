
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

import bpy
import nodeitems_utils
import bl_operators

import sverchok
from sverchok.core import sv_registration_utils, make_node_list
from sverchok.utils import auto_gather_node_classes
from sverchok.menu import SverchNodeItem, node_add_operators, SverchNodeCategory, register_node_panels, unregister_node_panels, unregister_node_add_operators, register_extra_category_provider
from sverchok.ui.nodeview_space_menu import make_extra_category_menus
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat

from . import sockets
from . import data

# make sverchok the root module name, (if sverchok dir not named exactly "sverchok") 
if __name__ != "sverchok_extra":
    sys.modules["sverchok_extra"] = sys.modules[__name__]

imported_modules = []

def nodes_index():
    return [("Surface", [
                ("surface.minimal_surface", "SvExMinimalSurfaceNode"),
                ("surface.smooth_spline", "SvExBivariateSplineNode"),
                ("surface.nurbs_surface", "SvExNurbsSurfaceNode"),
                ("surface.bend_along_nurbs_surface", "SvExBendAlongGeomdlSurface"),
                ("surface.marching_cubes", "SvExMarchingCubesNode"),
                ("surface.evaluate_min_surface", "SvExEvalMinimalSurfaceNode"),
                ("surface.evaluate_nurbs_surface", "SvExEvalNurbsSurfaceNode")
            ]),
            ("Curve", [
                ("curve.nurbs_curve", "SvExNurbsCurveNode")
            ]),
            ("Spatial", [
                ("spatial.voronoi3d", "SvExVoronoi3DNode")
            ])
    ]

def register_nodes():
    global imported_modules
    base_name = "sverchok_extra.nodes"
    index = nodes_index()
    for category, items in index:
        for module_name, node_name in items:
            module = importlib.import_module(f".{module_name}", base_name)
            imported_modules.append(module)
            module.register()

def unregister_nodes():
    global imported_modules
    for module in reversed(imported_modules):
        module.unregister()

def make_menu():
    menu = []
    index = nodes_index()
    for category, items in index:
        identifier = "SVERCHOK_EXTRA_" + category
        cat = SverchNodeCategory(
                    identifier,
                    category,
                    items = [SverchNodeItem.new(item[1]) for item in items]
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

def register():
    global our_menu_classes

    sockets.register()
    data.register()

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

def unregister():
    global our_menu_classes
    if 'SVERCHOK_EXTRA' in nodeitems_utils._node_categories:
        #unregister_node_panels()
        nodeitems_utils.unregister_node_categories("SVERCHOK_EXTRA")
    for clazz in our_menu_classes:
        bpy.utils.unregister_class(clazz)
    #unregister_node_add_operators()
    unregister_nodes()

    data.unregister()
    sockets.unregister()

