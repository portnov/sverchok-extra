
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
import logging

import nodeitems_utils

from sverchok.ui.nodeview_space_menu import add_node_menu

# make sverchok the root module name, (if sverchok dir not named exactly "sverchok")
if __name__ != "sverchok_extra":
    sys.modules["sverchok_extra"] = sys.modules[__name__]

from sverchok_extra import icons
from sverchok_extra import settings
from sverchok_extra.nodes_index import nodes_index
from sverchok_extra.utils import show_welcome

logger = logging.getLogger('sverchok.extra')

# Convert struct to menu.
# In:
#   - source struct
#   - lambda to convert tuples (final items are tuples in format ("{path}utils.o3d_import", "{class_name}SvO3ImportNode"))
def convert_config(obj, func=None):
    if not func:
        func = lambda elem: elem # call only on tuples
    cls_names = []
    if type(obj)==dict:
        cls_names = dict()

    for elem in obj:
        if elem==None: # this is menu items break
            cls_names.append( func(elem) )
        elif type(elem)==tuple:
            cls_names.append( func(elem) ) # this is menu item - tuple of two params
        elif type(obj)==dict:
            res = convert_config(obj[elem], func) # this is submenu
            if res:
                cls_names[elem]=res
        elif type(obj)==list:
            res = convert_config(elem, func)
            if res:
                cls_names.append(res)
        else:
            raise Exception("Menu struct error")
    return cls_names

# function as argument for convert_config. call only on tuples
def collect_classes_names(elem):
    if elem is None:
        res = '---'  # menu splitter. Used by Sverchok.
    elif isinstance(elem[0], dict): # property of menugroup, ex: ({'icon_name': 'MESH_BOX'}) for icon.
        res = elem[0]
    else:
        res = elem[1]  # class name to bind to menu Shift-A
    return res
nodes_items = convert_config(nodes_index(), collect_classes_names)
add_node_menu.append_from_config( nodes_items )

def make_node_list():
    modules = []
    base_name = "sverchok_extra.nodes"
    arr_items = []
    def collect_module_names(elem):
        if elem is not None:
            if isinstance(elem[0], str):
                arr_items.append(elem[0])
        return elem
    convert_config(nodes_index(), collect_module_names)
    for module_name in arr_items:
        module = importlib.import_module(f".{module_name}", base_name)
        modules.append(module)
    return modules

imported_modules = [icons] + make_node_list()

reload_event = False

if "bpy" in locals():
    reload_event = True
    logger.info("Reloading sverchok-extra...")

import bpy

def register_nodes():
    node_modules = make_node_list()
    for module in node_modules:
        module.register()
    logger.info("Registered %s nodes", len(node_modules))

def unregister_nodes():
    global imported_modules
    for module in reversed(imported_modules):
        module.unregister()


our_menu_classes = []

def reload_modules():
    global imported_modules
    for im in imported_modules:
        logger.debug("Reloading: %s", im)
        importlib.reload(im)

    util_modules = [m for p, m in sys.modules.items()
                    if p.startswith('sverchok_extra.utils')]
    for module in util_modules:
        importlib.reload(module)


if reload_event:
    reload_modules()


def register():
    global our_menu_classes

    logger.debug("Registering sverchok-extra")

    add_node_menu.register()
    settings.register()
    icons.register()

    register_nodes()
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
