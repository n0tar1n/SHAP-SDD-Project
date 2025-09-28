import os
import sys
from shap.compute_shap import compute_shap_scores
from sdd.sdd_utils import load_cnf, construct_sdd
from sdd.sdd_visualizer import sdd_to_dot  # Import visualization utility

def main(cnf_file):
    try:
        # Load the CNF DIMACS file
        cnf_formula = load_cnf(cnf_file)
        
        # Construct the SDD using a right-linear vtree
        sdd = construct_sdd(cnf_formula)
        
        # Compute SHAP scores
        shap_scores = compute_shap_scores(sdd)
        
        # Output the SHAP scores
        print("SHAP Scores:", shap_scores)
        
        # Ensure the output directory exists
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Visualize the SDD and save it as a DOT file
        dot_file_path = os.path.join(output_dir, "sdd.dot")
        with open(dot_file_path, "w") as sdd_out:
            print(sdd_to_dot(sdd), file=sdd_out)
        print(f"SDD visualization saved to '{dot_file_path}'.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_cnf_file>")
        sys.exit(1)
    
    main(sys.argv[1])