import time
import statistics
import csv
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# Allow "src" imports when running `python -m benchmarks.run`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sdd.sdd_utils import load_cnf, construct_sdd
from shap.compute_shap import compute_shap_scores
from utils.helpers import load_and_validate_json


# -----------------------------
# Optional: SHAP breakdown hook
# -----------------------------
def compute_shap_scores_with_breakdown(sdd, marginals, entity):
    """
    Default: calls compute_shap_scores and returns (scores, breakdown_dict_or_None).

    Supported returns from compute_shap_scores:
      A) scores
      B) (scores, breakdown_dict)
      C) {"scores": scores, "breakdown": {...}}
    """
    out = compute_shap_scores(sdd, marginals, entity)

    if isinstance(out, tuple) and len(out) == 2 and isinstance(out[1], dict):
        return out[0], out[1]

    if isinstance(out, dict) and "scores" in out:
        return out["scores"], out.get("breakdown")

    return out, None


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


@dataclass
class RunRecord:
    test_name: str
    run_idx: int

    load_time: float
    compile_time: float
    shap_time: float
    total_time: float

    sdd_size: int
    num_variables: int

    shap_breakdown: dict | None = None


@dataclass
class AggRecord:
    test_name: str
    num_variables: int
    sdd_size: int

    mean_compile: float
    mean_shap: float
    mean_total: float

    median_compile: float
    median_shap: float
    median_total: float

    stdev_compile: float
    stdev_shap: float
    stdev_total: float

    compile_pct_of_total: float
    shap_pct_of_total: float


def _safe_stdev(xs):
    return statistics.stdev(xs) if len(xs) >= 2 else 0.0


def benchmark_single_run(
    test_name: str,
    cnf_file: str,
    marginals_file: str,
    entity_file: str,
    *,
    reuse_sdd=None,
    reuse_inputs=None,
    shap_fn=compute_shap_scores_with_breakdown,
    measure_compile: bool = True,
):
    # Phase 1: Load inputs
    start_load = time.perf_counter()
    if reuse_inputs is None:
        cnf_formula = load_cnf(cnf_file)
        marginals, entity = load_and_validate_json(marginals_file, entity_file)
    else:
        cnf_formula, marginals, entity = reuse_inputs
    end_load = time.perf_counter()

    # Phase 2: Compile SDD (optional / reusable)
    if reuse_sdd is not None or not measure_compile:
        sdd = reuse_sdd
        compile_time = 0.0
    else:
        start_compile = time.perf_counter()
        sdd = construct_sdd(cnf_formula)
        end_compile = time.perf_counter()
        compile_time = end_compile - start_compile

    sdd_size = count_sdd_nodes(sdd)

    # Phase 3: Compute SHAP
    start_shap = time.perf_counter()
    shap_scores, shap_breakdown = shap_fn(sdd, marginals, entity)
    end_shap = time.perf_counter()

    total_time = (
        (end_shap - start_load)
        if (reuse_sdd is None and measure_compile)
        else ((end_load - start_load) + (end_shap - start_shap))
    )

    return {
        "load_time": end_load - start_load,
        "compile_time": compile_time,
        "shap_time": end_shap - start_shap,
        "total_time": total_time,
        "sdd_size": sdd_size,
        "num_variables": len(marginals),
        "shap_scores": shap_scores,  # kept if needed
        "shap_breakdown": shap_breakdown,
    }


def run_benchmark(
    test_name: str,
    cnf_file: str,
    marginals_file: str,
    entity_file: str,
    *,
    num_runs: int = 10,
    warmup: int = 1,
    cache_inputs: bool = True,
    cache_sdd: bool = False,
    shap_fn=compute_shap_scores_with_breakdown,
    verbose: bool = True,
):
    if verbose:
        print(f"\nBenchmarking: {test_name}")
        print(f"CNF: {cnf_file}")
        print(f"Runs: {num_runs} (+{warmup} warmup)")
        print(f"cache_inputs={cache_inputs}, cache_sdd={cache_sdd}")
        print("-" * 70)

    reuse_inputs = None
    if cache_inputs:
        cnf_formula = load_cnf(cnf_file)
        marginals, entity = load_and_validate_json(marginals_file, entity_file)
        reuse_inputs = (cnf_formula, marginals, entity)

    reuse_sdd = None
    if cache_sdd:
        cnf_formula = reuse_inputs[0] if reuse_inputs else load_cnf(cnf_file)
        reuse_sdd = construct_sdd(cnf_formula)

    # Warmup (not recorded)
    for _ in range(warmup):
        _ = benchmark_single_run(
            test_name, cnf_file, marginals_file, entity_file,
            reuse_sdd=reuse_sdd,
            reuse_inputs=reuse_inputs,
            shap_fn=shap_fn,
            measure_compile=(not cache_sdd),
        )

    records: list[RunRecord] = []
    first_meta_printed = False

    for i in range(num_runs):
        r = benchmark_single_run(
            test_name, cnf_file, marginals_file, entity_file,
            reuse_sdd=reuse_sdd,
            reuse_inputs=reuse_inputs,
            shap_fn=shap_fn,
            measure_compile=(not cache_sdd),
        )

        rec = RunRecord(
            test_name=test_name,
            run_idx=i,
            load_time=r["load_time"],
            compile_time=r["compile_time"],
            shap_time=r["shap_time"],
            total_time=r["total_time"],
            sdd_size=r["sdd_size"],
            num_variables=r["num_variables"],
            shap_breakdown=r["shap_breakdown"],
        )
        records.append(rec)

        if verbose and not first_meta_printed:
            first_meta_printed = True
            print(f"Variables: {rec.num_variables}")
            print(f"SDD Size:  {rec.sdd_size} nodes")

    return records


def aggregate(records: list[RunRecord]) -> AggRecord:
    compile_times = [r.compile_time for r in records]
    shap_times = [r.shap_time for r in records]
    total_times = [r.total_time for r in records]

    num_vars = records[0].num_variables
    sdd_size = records[0].sdd_size
    test_name = records[0].test_name

    mean_compile = statistics.mean(compile_times)
    mean_shap = statistics.mean(shap_times)
    mean_total = statistics.mean(total_times)

    return AggRecord(
        test_name=test_name,
        num_variables=num_vars,
        sdd_size=sdd_size,

        mean_compile=mean_compile,
        mean_shap=mean_shap,
        mean_total=mean_total,

        median_compile=statistics.median(compile_times),
        median_shap=statistics.median(shap_times),
        median_total=statistics.median(total_times),

        stdev_compile=_safe_stdev(compile_times),
        stdev_shap=_safe_stdev(shap_times),
        stdev_total=_safe_stdev(total_times),

        compile_pct_of_total=(mean_compile / mean_total * 100.0) if mean_total > 0 else 0.0,
        shap_pct_of_total=(mean_shap / mean_total * 100.0) if mean_total > 0 else 0.0,
    )


def print_stats(records: list[RunRecord]):
    load_times = [r.load_time for r in records]
    compile_times = [r.compile_time for r in records]
    shap_times = [r.shap_time for r in records]
    total_times = [r.total_time for r in records]

    def fmt(label, xs):
        print(f"\n{label}:")
        print(f"  Mean:   {statistics.mean(xs)*1000:.2f} ms")
        print(f"  Median: {statistics.median(xs)*1000:.2f} ms")
        print(f"  StdDev: {_safe_stdev(xs)*1000:.2f} ms")

    fmt("Load Time", load_times)
    fmt("Compile Time", compile_times)
    fmt("SHAP Time", shap_times)
    fmt("Total Time", total_times)

    avg_load = statistics.mean(load_times)
    avg_compile = statistics.mean(compile_times)
    avg_shap = statistics.mean(shap_times)
    avg_total = statistics.mean(total_times)

    print("\nTime Breakdown (mean % of total):")
    if avg_total > 0:
        print(f"  Load/Validation: {avg_load/avg_total*100:.1f}%")
        print(f"  SDD Compilation: {avg_compile/avg_total*100:.1f}%")
        print(f"  SHAP Computation:{avg_shap/avg_total*100:.1f}%")
    else:
        print("  (total time is 0?)")


def export_aggregates_csv(aggs: list[AggRecord], path: str):
    if not aggs:
        return
    fieldnames = list(asdict(aggs[0]).keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for a in aggs:
            w.writerow(asdict(a))


def export_records_csv(records: list[RunRecord], path: str):
    if not records:
        return

    def row(r: RunRecord):
        d = asdict(r)
        d["shap_breakdown"] = str(r.shap_breakdown) if r.shap_breakdown is not None else ""
        return d

    fieldnames = list(row(records[0]).keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in records:
            w.writerow(row(r))
