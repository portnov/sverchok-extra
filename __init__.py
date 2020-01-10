
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
from sverchok.menu import SverchNodeItem, node_add_operators, SverchNodeCategory, register_node_panels, unregister_node_panels, unregister_node_add_operators
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat

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
                ("surface.marching_cubes", "SvExMarchingCubesNode")
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
        menu.append(
                SverchNodeCategory(
                    "SVERCHOK_EXTRA_" + category,
                    category,
                    items = [SverchNodeItem.new(item[1]) for item in items]
                )
            )
    return menu

def register():
    register_nodes()
    extra_nodes = importlib.import_module(".nodes", "sverchok_extra")
    auto_gather_node_classes(extra_nodes)    
    menu = make_menu()
    #if 'SVERCHOK_EXTRA' in nodeitems_utils._node_categories:
        #unregister_node_panels()
        #nodeitems_utils.unregister_node_categories("SVERCHOK_EXTRA")
    nodeitems_utils.register_node_categories("SVERCHOK_EXTRA", menu)
    #register_node_panels("SVERCHOK_EXTRA", menu)

def unregister():
    if 'SVERCHOK_EXTRA' in nodeitems_utils._node_categories:
        #unregister_node_panels()
        nodeitems_utils.unregister_node_categories("SVERCHOK_EXTRA")
    #unregister_node_add_operators()
    unregister_nodes()

