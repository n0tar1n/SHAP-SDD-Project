from .core import (
    run_benchmark,
    aggregate,
    print_stats,
    export_records_csv,
    export_aggregates_csv,
)
from .views import (
    view_1_compilation_vs_shap,
    view_2_runtime_vs_circuit_size,
    view_3_compile_vs_shap_cost_breakdown,
    view_4_shap_runtime_vs_num_variables,
)


def main():
    test_cases = [
        {
            "name": "Small (2 vars, 4 clauses) - Symmetric",
            "cnf": "tests/data/small/formula.cnf",
            "marginals": "tests/data/small/product.json",
            "entity": "tests/data/small/entity.json",
        },
        {
            "name": "Medium (4 vars, 2 clauses) - Independent OR",
            "cnf": "tests/data/medium/formula.cnf",
            "marginals": "tests/data/medium/product.json",
            "entity": "tests/data/medium/entity.json",
        },
        {
            "name": "Large (5 vars, 10 clauses) - Constraint SAT",
            "cnf": "tests/data/large/formula.cnf",
            "marginals": "tests/data/large/product.json",
            "entity": "tests/data/large/entity.json",
        },
    ]

    all_run_records = []
    per_test_records = {}

    for tc in test_cases:
        print(f"\n{'='*70}")
        print(f"TEST CASE: {tc['name']}")
        print(f"{'='*70}")

        records = run_benchmark(
            tc["name"],
            tc["cnf"],
            tc["marginals"],
            tc["entity"],
            num_runs=20,
            warmup=1,
            cache_inputs=True,
            cache_sdd=False,  # keep compile timings for benchmark #1 and #3
            verbose=True,
        )

        print_stats(records)

        per_test_records[tc["name"]] = records
        all_run_records.extend(records)

    aggs = [aggregate(per_test_records[tc["name"]]) for tc in test_cases]

    # 4 benchmark views
    view_1_compilation_vs_shap(aggs)
    view_2_runtime_vs_circuit_size(aggs, runtime_field="mean_shap")
    view_3_compile_vs_shap_cost_breakdown(aggs)
    view_4_shap_runtime_vs_num_variables(aggs)

    # CSV exports
    export_records_csv(all_run_records, "benchmark_runs.csv")
    export_aggregates_csv(aggs, "benchmark_aggregates.csv")

    print("\nSaved:")
    print("  - benchmark_runs.csv")
    print("  - benchmark_aggregates.csv")


if __name__ == "__main__":
    main()
