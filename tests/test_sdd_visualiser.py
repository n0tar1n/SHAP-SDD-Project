import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import unittest
from pysdd.sdd import SddManager, Vtree
from sdd.sdd_visualizer import sdd_to_dot

class TestSddVisualizer(unittest.TestCase):
    def test_sdd_to_dot(self):
        """
        Tests that the sdd_to_dot function produces valid DOT output for an SDD node.
        The test case creates an SDD node representing the formula a & b, converts it to DOT format,
        and checks that the output contains the expected strings.
        """
        vtree = Vtree(var_count=2, vtree_type="right")
        sdd_manager = SddManager.from_vtree(vtree)
        a, b = sdd_manager.vars
        formula = a & b

        # Define a literal name map for the test
        litnamemap = {1: "a", 2: "b", -1: "¬a", -2: "¬b"}

        dot_output = sdd_to_dot(formula, litnamemap=litnamemap)
        self.assertIn("digraph SDD {", dot_output)
        self.assertIn(f'{a.id} [label="a"];', dot_output)
        self.assertIn(f'{b.id} [label="b"];', dot_output)
        self.assertIn("}", dot_output)

if __name__ == "__main__":
    unittest.main()