import os
import sys
import argparse
from shap.compute_shap import compute_shap_scores
from sdd.sdd_utils import load_cnf, construct_sdd
from utils.helpers import load_and_validate_json
def main():
    parser = argparse.ArgumentParser(description='Compute SHAP scores for CNF formulas')
    parser.add_argument('cnf_file', help='Path to CNF file')
    parser.add_argument('--marginals', required=True, help='Path to product distribution JSON file')
    parser.add_argument('--entity', required=True, help='Path to input instance JSON file')
    
    args = parser.parse_args()
    
    try:
        # Load and validate JSON files 
        marginals, entity = load_and_validate_json(args.marginals, args.entity)
        
        print(f"✓ JSON validation passed")
        print(f"CNF file: {args.cnf_file}")
        print(f"Marginals: {marginals}")
        print(f"Entity: {entity}")
        
        # Load the CNF DIMACS file
        cnf_formula = load_cnf(args.cnf_file)
        
        # Construct the SDD using a right-linear vtree
        sdd = construct_sdd(cnf_formula)
        
        # Compute SHAP scores with marginals and entity
        shap_scores = compute_shap_scores(sdd, marginals, entity)
        
        print("\nSHAP Scores:")
        for var, score in sorted(shap_scores.items()):
            print(f"  {var}: {score:.6f}")
        
    except (ValueError, Exception) as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()