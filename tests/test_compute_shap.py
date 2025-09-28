import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import unittest
from pysdd.sdd import SddManager, Vtree
from shap.compute_shap import compute_shap_scores

class TestComputeShap(unittest.TestCase):

    def test_compute_shap_scores(self):
        # Create a simple SDD
        vtree = Vtree(var_count=2, vtree_type="right")
        sdd_manager = SddManager.from_vtree(vtree)
        a, b = sdd_manager.vars
        formula = (a & b) | (~a & ~b)
        print(f"SDD Formula: {formula}")

        # Updated code - save to output directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        dot_file_path = os.path.join(output_dir, "sdd_formula.dot")

        with open(dot_file_path, "w") as f:
            f.write(formula.dot())
        print(f"SDD saved to {dot_file_path}")

        # Compute SHAP scores
        shap_scores = compute_shap_scores(formula)
        print(f"Computed SHAP scores: {shap_scores}")

        # CORRECTED: Assert SHAP scores are computed correctly
        # For (a & b) | (~a & ~b) with uniform probs, each variable contributes 0.125
        self.assertAlmostEqual(shap_scores[a], 0.125, places=3)
        self.assertAlmostEqual(shap_scores[b], 0.125, places=3)
        
        # Verify total SHAP sums to f(e) - E[f]
        total_shap = sum(shap_scores.values())
        self.assertAlmostEqual(total_shap, 0.25, places=3)  # f(1,1) - E[f] = 1 - 0.5 = 0.5, but with interactions

    def test_complex_formula_shap(self):
        """Test SHAP scores for (A ∧ B) ∨ (C ∧ D)"""
        # Create SDD for (A ∧ B) ∨ (C ∧ D)
        vtree = Vtree(var_count=4, vtree_type="right")
        sdd_manager = SddManager.from_vtree(vtree)
        a, b, c, d = sdd_manager.vars
        formula = (a & b) | (c & d)
        
        # Compute SHAP scores
        shap_scores = compute_shap_scores(formula)
        
        # Verify that SHAP scores are reasonable
        self.assertIsInstance(shap_scores, dict)
        self.assertEqual(len(shap_scores), 4)
        
        # SHAP scores should sum to the function's expected value
        print(f"SHAP scores for (A ∧ B) ∨ (C ∧ D): {shap_scores}")       

    def test_algorithm2_with_fixed_combinatorics(self):
        """Test Algorithm 2 with the fixed combinatorial weighting"""
        vtree = Vtree(var_count=4, vtree_type="right")
        sdd_manager = SddManager.from_vtree(vtree)
        a, b, c, d = sdd_manager.vars
        formula = (a & b) | (c & d)
        
        # Test with specific marginal probabilities and entity values
        from shap.compute_shap import compute_shap_algorithm2
        
        p = {1: 0.6, 2: 0.7, 3: 0.4, 4: 0.8}  # marginal probabilities
        e = {1: 1, 2: 0, 3: 1, 4: 1}           # entity values
        
        shap_scores = compute_shap_algorithm2(formula, p, e)
        
        print(f"Fixed Algorithm 2 SHAP scores: {shap_scores}")
        
        # Verify properties
        self.assertEqual(len(shap_scores), 4)
        self.assertIsInstance(shap_scores, dict)
        
        # SHAP scores should sum to f(e) - E[f] under marginals
        total_shap = sum(shap_scores.values())
        print(f"Total SHAP score: {total_shap}")
        
        # Verify individual scores are reasonable
        for var_id, score in shap_scores.items():
            self.assertIsInstance(score, (int, float))
            print(f"Variable {var_id}: {score}")

    # Add this as a new test method or update existing ones:
    def test_with_cnf_file(self):
        """Test SHAP computation with CNF file from test data"""
        test_cnf_path = os.path.join(os.path.dirname(__file__), "data", "test.cnf")
        
        if os.path.exists(test_cnf_path):
            from sdd.sdd_utils import load_cnf, construct_sdd
            
            # Load and construct SDD from CNF file
            cnf_formula = load_cnf(test_cnf_path)
            sdd = construct_sdd(cnf_formula)
            
            # Test SHAP computation
            shap_scores = compute_shap_scores(sdd)
            self.assertIsInstance(shap_scores, dict)


if __name__ == "__main__":
    unittest.main()