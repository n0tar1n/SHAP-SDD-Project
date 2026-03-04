from pathlib import Path
from datetime import datetime
import json

from .core import (
    run_benchmark,
    aggregate,
    export_records_csv,
    export_aggregates_csv,
    print_stats,
)
from .views import (
    view_1_compilation_vs_shap,
    view_2_runtime_vs_circuit_size,
    view_3_compile_vs_shap_cost_breakdown,
    view_4_shap_runtime_vs_num_variables,
)


def parse_dimacs_header(cnf_path: Path):
    with cnf_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("p "):
                parts = line.strip().split()
                # p cnf <num_vars> <num_clauses>
                if len(parts) >= 4 and parts[1] == "cnf":
                    return int(parts[2]), int(parts[3])
    raise ValueError(f"No DIMACS header found in {cnf_path}")


def make_output_dir(test_cases: list[dict], results_root: Path) -> Path:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if len(test_cases) == 1:
        cnf_stem = Path(test_cases[0]["cnf"]).stem
        out_dir = results_root / cnf_stem / run_id
    else:
        out_dir = results_root / f"batch_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def main():
    ace_dir = Path("benchmarks/BayesianNetwork/Ace")
    inputs_root = ace_dir / "inputs"

    # Output base folder (create this automatically)
    results_root = Path("results") / "ace"
    results_root.mkdir(parents=True, exist_ok=True)

    # --- tune skip thresholds ---
    MAX_VARS = 6000
    MAX_MB = 1.0

    # --- which CNFs to run ---
    # For a single file
    cnfs = [ace_dir / "fs-01.net.cnf"]
    # cnfs = [ace_dir / "blockmap_05_01.net.cnf"]

    # For all files (will be filtered by thresholds and input availability)
    # cnfs = sorted(ace_dir.glob("*.cnf"))

    skipped = []  # (name, reason)
    test_cases = []

    for cnf in cnfs:
        size_mb = cnf.stat().st_size / (1024 * 1024)
        try:
            nvars, nclauses = parse_dimacs_header(cnf)
        except Exception as e:
            skipped.append((cnf.name, f"header parse failed: {e}"))
            continue

        if nvars > MAX_VARS or size_mb > MAX_MB:
            skipped.append((cnf.name, f"skip vars={nvars}, size={size_mb:.2f}MB"))
            continue

        case_dir = inputs_root / cnf.stem
        marg = case_dir / "product.json"
        ent = case_dir / "entity.json"

        if not marg.exists() or not ent.exists():
            skipped.append((cnf.name, f"missing inputs in {case_dir}"))
            continue

        test_cases.append(
            {
                "name": f"Ace/{cnf.stem} (vars={nvars}, clauses={nclauses})",
                "cnf": str(cnf),
                "marginals": str(marg),
                "entity": str(ent),
                "nvars": nvars,
                "nclauses": nclauses,
                "size_mb": size_mb,
            }
        )

    print(f"\nWill benchmark {len(test_cases)} Ace CNFs\n")
    if skipped:
        print("Skipped CNFs:")
        for name, reason in skipped:
            print(f"  - {name}: {reason}")

    if not test_cases:
        print("\nNo test cases to run (all skipped or missing inputs).")
        return

    out_dir = make_output_dir(test_cases, results_root)
    print(f"\nOutputs will be saved to:\n  {out_dir}\n")

    # --- benchmark settings ---
    NUM_RUNS = 5
    WARMUP = 1
    CACHE_INPUTS = True
    CACHE_SDD = False
    VERBOSE = True

    all_run_records = []
    per_test_records = {}

    for tc in test_cases:
        print(f"\n{'='*70}\nTEST CASE: {tc['name']}\n{'='*70}")
        try:
            records = run_benchmark(
                tc["name"],
                tc["cnf"],
                tc["marginals"],
                tc["entity"],
                num_runs=NUM_RUNS,
                warmup=WARMUP,
                cache_inputs=CACHE_INPUTS,
                cache_sdd=CACHE_SDD,
                verbose=VERBOSE,
            )
        except MemoryError:
            print(f"[FAIL-SKIP] MemoryError on {tc['name']}")
            skipped.append((Path(tc["cnf"]).name, "MemoryError during run"))
            continue
        except Exception as e:
            print(f"[FAIL-SKIP] {tc['name']}: {type(e).__name__}: {e}")
            skipped.append((Path(tc["cnf"]).name, f"{type(e).__name__}: {e}"))
            continue

        print_stats(records)
        per_test_records[tc["name"]] = records
        all_run_records.extend(records)

    if not all_run_records:
        print("No successful runs.")
        return

    aggs = [aggregate(per_test_records[name]) for name in per_test_records.keys()]

    # Views (these may pop up windows depending on your matplotlib backend)
    view_1_compilation_vs_shap(aggs)
    view_2_runtime_vs_circuit_size(aggs, runtime_field="mean_shap")
    view_3_compile_vs_shap_cost_breakdown(aggs)
    view_4_shap_runtime_vs_num_variables(aggs)

    # Save CSV outputs into the run folder
    export_records_csv(all_run_records, str(out_dir / "benchmark_runs.csv"))
    export_aggregates_csv(aggs, str(out_dir / "benchmark_aggregates.csv"))

    # Save metadata for reproducibility
    meta = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "ace_dir": str(ace_dir),
        "inputs_root": str(inputs_root),
        "output_dir": str(out_dir),
        "settings": {
            "MAX_VARS": MAX_VARS,
            "MAX_MB": MAX_MB,
            "NUM_RUNS": NUM_RUNS,
            "WARMUP": WARMUP,
            "CACHE_INPUTS": CACHE_INPUTS,
            "CACHE_SDD": CACHE_SDD,
            "VERBOSE": VERBOSE,
        },
        "ran": [
            {
                "name": tc["name"],
                "cnf": tc["cnf"],
                "marginals": tc["marginals"],
                "entity": tc["entity"],
                "nvars": tc["nvars"],
                "nclauses": tc["nclauses"],
                "size_mb": tc["size_mb"],
            }
            for tc in test_cases
        ],
        "skipped": skipped,
    }
    with (out_dir / "meta.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("\nSaved:")
    print(f"  - {out_dir / 'benchmark_runs.csv'}")
    print(f"  - {out_dir / 'benchmark_aggregates.csv'}")
    print(f"  - {out_dir / 'meta.json'}")


if __name__ == "__main__":
    main()