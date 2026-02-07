import time
import timeit
import statistics
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sdd.sdd_utils import load_cnf, construct_sdd
from shap.compute_shap import compute_shap_scores
from utils.helpers import load_and_validate_json


def benchmark_single_run(cnf_file, marginals_file, entity_file):
    """Times a single end-to-end SHAP computation."""
    
    # Phase 1: Load inputs
    start_load = time.perf_counter()
    cnf_formula = load_cnf(cnf_file)
    marginals, entity = load_and_validate_json(marginals_file, entity_file)
    end_load = time.perf_counter()
    
    # Phase 2: Compile SDD
    start_compile = time.perf_counter()
    sdd = construct_sdd(cnf_formula)
    end_compile = time.perf_counter()
    
    # Phase 3: Compute SHAP
    start_shap = time.perf_counter()
    shap_scores = compute_shap_scores(sdd, marginals, entity)
    end_shap = time.perf_counter()
    
    return {
        'load_time': end_load - start_load,
        'compile_time': end_compile - start_compile,
        'shap_time': end_shap - start_shap,
        'total_time': end_shap - start_load,
        'sdd_size': count_sdd_nodes(sdd),
        'num_variables': len(marginals),
        'shap_scores': shap_scores
    }


def count_sdd_nodes(sdd):
    """Counts total nodes in SDD."""
    visited = set()
    
    def traverse(node):
        if node.id in visited:
            return 0
        visited.add(node.id)
        
        if node.is_true() or node.is_false() or node.is_literal():
            return 1
        
        count = 1
        for prime, sub in node.elements():
            count += traverse(prime)
            count += traverse(sub)
        return count
    
    return traverse(sdd)


def run_benchmark(cnf_file, marginals_file, entity_file, num_runs=10):
    """Runs multiple iterations and computes statistics."""
    print(f"\nBenchmarking: {cnf_file}")
    print(f"Number of runs: {num_runs}")
    print("-" * 60)
    
    results = []
    for i in range(num_runs):
        result = benchmark_single_run(cnf_file, marginals_file, entity_file)
        results.append(result)
        if i == 0:
            print(f"Variables: {result['num_variables']}")
            print(f"SDD Size: {result['sdd_size']} nodes")
    
    # Compute statistics
    load_times = [r['load_time'] for r in results]
    compile_times = [r['compile_time'] for r in results]
    shap_times = [r['shap_time'] for r in results]
    total_times = [r['total_time'] for r in results]
    
    print(f"\nLoad Time:")
    print(f"  Mean:   {statistics.mean(load_times)*1000:.2f} ms")
    print(f"  Median: {statistics.median(load_times)*1000:.2f} ms")
    print(f"  StdDev: {statistics.stdev(load_times)*1000:.2f} ms")
    
    print(f"\nCompile Time:")
    print(f"  Mean:   {statistics.mean(compile_times)*1000:.2f} ms")
    print(f"  Median: {statistics.median(compile_times)*1000:.2f} ms")
    print(f"  StdDev: {statistics.stdev(compile_times)*1000:.2f} ms")
    
    print(f"\nSHAP Computation Time:")
    print(f"  Mean:   {statistics.mean(shap_times)*1000:.2f} ms")
    print(f"  Median: {statistics.median(shap_times)*1000:.2f} ms")
    print(f"  StdDev: {statistics.stdev(shap_times)*1000:.2f} ms")
    
    print(f"\nTotal Time:")
    print(f"  Mean:   {statistics.mean(total_times)*1000:.2f} ms")
    print(f"  Median: {statistics.median(total_times)*1000:.2f} ms")
    print(f"  StdDev: {statistics.stdev(total_times)*1000:.2f} ms")
    
    # Compute percentage breakdown
    avg_load = statistics.mean(load_times)
    avg_compile = statistics.mean(compile_times)
    avg_shap = statistics.mean(shap_times)
    avg_total = statistics.mean(total_times)
    
    print(f"\nTime Breakdown:")
    print(f"  Load/Validation: {avg_load/avg_total*100:.1f}%")
    print(f"  SDD Compilation: {avg_compile/avg_total*100:.1f}%")
    print(f"  SHAP Computation: {avg_shap/avg_total*100:.1f}%")
    
    return results

"""
if __name__ == "__main__":
    # Benchmark different formula sizes
    test_cases = [
        {
            'name': 'Small (2 vars, 4 clauses) - Symmetric',
            'cnf': 'tests/data/small/formula.cnf',
            'marginals': 'tests/data/small/product.json',
            'entity': 'tests/data/small/entity.json'
        },
        {
            'name': 'Medium (4 vars, 2 clauses) - Independent OR',
            'cnf': 'tests/data/medium/formula.cnf',
            'marginals': 'tests/data/medium/product.json',
            'entity': 'tests/data/medium/entity.json'
        },
        {
            'name': 'Large (5 vars, 10 clauses) - Constraint SAT',
            'cnf': 'tests/data/large/formula.cnf',
            'marginals': 'tests/data/large/product.json',
            'entity': 'tests/data/large/entity.json'
        }
    ]
    
    all_results = {}
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"TEST CASE: {test_case['name']}")
        print(f"{'='*60}")
        
        results = run_benchmark(
            test_case['cnf'],
            test_case['marginals'],
            test_case['entity'],
            num_runs=20
        )
        all_results[test_case['name']] = results
    
    # Summary table
    print(f"\n{'='*60}")
    print("SUMMARY TABLE")
    print(f"{'='*60}")
    print(f"{'Test Case':<45} {'Vars':<6} {'SDD':<8} {'Compile':<10} {'SHAP':<10} {'Total':<10}")
    print(f"{'-'*45} {'-'*6} {'-'*8} {'-'*10} {'-'*10} {'-'*10}")
    
    for test_case in test_cases:
        results = all_results[test_case['name']]
        avg_compile = statistics.mean([r['compile_time'] for r in results]) * 1000
        avg_shap = statistics.mean([r['shap_time'] for r in results]) * 1000
        avg_total = statistics.mean([r['total_time'] for r in results]) * 1000
        num_vars = results[0]['num_variables']
        sdd_size = results[0]['sdd_size']
        
        print(f"{test_case['name']:<45} {num_vars:<6} {sdd_size:<8} "
              f"{avg_compile:<10.2f} {avg_shap:<10.2f} {avg_total:<10.2f}")
"""