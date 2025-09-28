import sys
import os
import unittest

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from sdd.sdd_utils import load_cnf, construct_sdd

class TestSddUtils(unittest.TestCase):
    def test_load_cnf(self):
        # Create a temporary CNF file
        cnf_content = "p cnf 2 2\n1 -2 0\n-1 2 0\n"
        with open("test.cnf", "w") as file:
            file.write(cnf_content)

        # Load the CNF file
        loaded_cnf = load_cnf("test.cnf")
        self.assertEqual(loaded_cnf, cnf_content)
        
        # Clean up the temporary file
        os.remove("test.cnf")

    def test_construct_sdd(self):
        # CNF formula as a string
        cnf_formula = "p cnf 2 2\n1 -2 0\n-1 2 0\n"

        # Construct the SDD
        sdd = construct_sdd(cnf_formula)

        # Assert that the SDD is not None
        self.assertIsNotNone(sdd)

if __name__ == "__main__":
    unittest.main()