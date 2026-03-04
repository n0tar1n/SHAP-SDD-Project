from pathlib import Path
import json
import random

def parse_dimacs_header(cnf_path: Path):
    with cnf_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("p "):
                parts = line.strip().split()
                # p cnf <num_vars> <num_clauses>
                if len(parts) >= 4 and parts[1] == "cnf":
                    return int(parts[2]), int(parts[3])
    raise ValueError(f"No DIMACS header found in {cnf_path}")

def write_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        # compact JSON to keep file sizes down
        json.dump(obj, f, separators=(",", ":"))

def main():
    ace_dir = Path("benchmarks/BayesianNetwork/Ace")
    out_root = ace_dir / "inputs"

    # --- skip thresholds ---
    MAX_VARS = 6000          # start conservative
    MAX_MB = 1.0             # skip big files by size too

    # --- value choices ---
    MARGINAL_DEFAULT = 0.5
    ENTITY_SEED_BASE = 42    # deterministic

    cnfs = sorted(ace_dir.glob("*.cnf"))
    print(f"Found {len(cnfs)} CNFs in {ace_dir}")

    skipped = []
    generated = []

    for cnf_path in cnfs:
        size_mb = cnf_path.stat().st_size / (1024 * 1024)
        try:
            nvars, nclauses = parse_dimacs_header(cnf_path)
        except Exception as e:
            skipped.append((cnf_path.name, f"header parse failed: {e}"))
            continue

        if nvars > MAX_VARS or size_mb > MAX_MB:
            skipped.append((cnf_path.name, f"skip vars={nvars}, size={size_mb:.2f}MB"))
            continue

        case_dir = out_root / cnf_path.stem
        prod_path = case_dir / "product.json"
        ent_path = case_dir / "entity.json"

        marginals = {f"x{i}": MARGINAL_DEFAULT for i in range(1, nvars + 1)}

        rng = random.Random(f"{ENTITY_SEED_BASE}:{cnf_path.stem}")
        entity = {f"x{i}": rng.randint(0, 1) for i in range(1, nvars + 1)}

        write_json(prod_path, marginals)
        write_json(ent_path, entity)
        generated.append((cnf_path.name, nvars, nclauses))

    print("\nGenerated inputs for:")
    for name, v, c in generated:
        print(f"  {name}: vars={v}, clauses={c}")

    print("\nSkipped:")
    for name, reason in skipped:
        print(f"  {name}: {reason}")

if __name__ == "__main__":
    main()