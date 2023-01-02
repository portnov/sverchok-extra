
import json

import bpy

def execute_tree(inputs, tree_name = 'NodeTree', input_node_name = 'API Input'):
    tree = bpy.data.node_groups[tree_name]
    input_node = tree.nodes[input_node_name]
    if input_node.bl_idname != 'SvExApiInNode':
        raise Exception(f"Node {input_node_name} in {tree_name} is not an API Input node")
    input_node.input_data = json.dumps(inputs)
    tree.process_ani(True,False)
    output_node = input_node.outputs['API'].links[0].to_node
    result = json.loads(output_node.output_data)
    print("R", result)
    return result
