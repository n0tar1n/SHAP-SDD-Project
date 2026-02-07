from .core import AggRecord


def view_1_compilation_vs_shap(aggs: list[AggRecord]):
    print(f"\n{'='*70}")
    print("BENCHMARK 1: Compilation vs SHAP runtime (means, ms)")
    print(f"{'='*70}")
    print(f"{'Test Case':<45} {'Compile(ms)':>12} {'SHAP(ms)':>12} {'Total(ms)':>12}")
    print(f"{'-'*45} {'-'*12} {'-'*12} {'-'*12}")
    for a in aggs:
        print(f"{a.test_name:<45} {a.mean_compile*1000:>12.2f} {a.mean_shap*1000:>12.2f} {a.mean_total*1000:>12.2f}")


def view_2_runtime_vs_circuit_size(aggs: list[AggRecord], runtime_field: str = "mean_shap"):
    """
    runtime_field in {"mean_shap", "mean_total", "mean_compile"}.
    Default uses SHAP runtime vs SDD size.
    """
    print(f"\n{'='*70}")
    print(f"BENCHMARK 2: Runtime vs circuit size (SDD nodes) [{runtime_field}]")
    print(f"{'='*70}")
    print(f"{'Test Case':<45} {'SDD(nodes)':>12} {'Runtime(ms)':>12}")
    print(f"{'-'*45} {'-'*12} {'-'*12}")

    for a in sorted(aggs, key=lambda x: x.sdd_size):
        runtime = getattr(a, runtime_field) * 1000
        print(f"{a.test_name:<45} {a.sdd_size:>12} {runtime:>12.2f}")


def view_3_compile_vs_shap_cost_breakdown(aggs: list[AggRecord]):
    print(f"\n{'='*70}")
    print("BENCHMARK 3: Compilation vs SHAP cost breakdown (mean % of total)")
    print(f"{'='*70}")
    print(f"{'Test Case':<45} {'Compile%':>10} {'SHAP%':>10} {'(rest)':>10}")
    print(f"{'-'*45} {'-'*10} {'-'*10} {'-'*10}")

    for a in aggs:
        rest = max(0.0, 100.0 - a.compile_pct_of_total - a.shap_pct_of_total)
        print(f"{a.test_name:<45} {a.compile_pct_of_total:>10.1f} {a.shap_pct_of_total:>10.1f} {rest:>10.1f}")


def view_4_shap_runtime_vs_num_variables(aggs: list[AggRecord]):
    print(f"\n{'='*70}")
    print("BENCHMARK 4: SHAP runtime vs number of variables (means)")
    print(f"{'='*70}")
    print(f"{'Test Case':<45} {'Vars':>8} {'SHAP(ms)':>12}")
    print(f"{'-'*45} {'-'*8} {'-'*12}")

    for a in sorted(aggs, key=lambda x: x.num_variables):
        print(f"{a.test_name:<45} {a.num_variables:>8} {a.mean_shap*1000:>12.2f}")
