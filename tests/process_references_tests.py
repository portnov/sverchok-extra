
from os.path import basename, dirname, join
from glob import glob
import unittest

from sverchok.utils.testing import SverchokTestCase, link_node_tree, get_node_tree, remove_node_tree
from sverchok.utils.logging import info, debug, error, exception

from sverchok_extra.testing import get_tests_path

#@unittest.skip
class ProcessRefsTestCase(SverchokTestCase):
    def test_import_examples(self):
        refs_path = join(get_tests_path(), "references")
        TREE_NAME = "NodeTree"
        remove_node_tree(TREE_NAME)
        for blend_path in glob(join(refs_path, "extra_*.blend.gz")):
            info("Testing: %s", blend_path)
            with self.subTest(file = blend_path):
                try:
                    with self.assert_logs_no_errors():
                        link_node_tree(blend_path, TREE_NAME)
                        tree = get_node_tree(TREE_NAME)
                        #tree.process()
                finally:
                    remove_node_tree(TREE_NAME)

