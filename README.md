# SHAP-SDD Project

## Overview

The **SHAP-SDD Project** provides an implementation of Algorithm 2 from the SDD research paper to compute SHAP (SHapley Additive exPlanations) values for models represented as **Sentential Decision Diagrams (SDDs)**. This toolkit enables interpretable machine learning for complex Boolean models, with support for CNF inputs, visualization, and robust testing.

---

## Features

- **Exact SHAP Score Computation:** Implements Algorithm 2 for bottom-up computation using γ (gamma) and δ (delta) arrays.
- **SDD Compilation:** Converts CNF files (DIMACS format) to right-linear SDDs with automatic vtree construction.
- **Visualization:** Generates DOT files for visualizing SDDs (via Graphviz).
- **Robust Data Validation:** Ensures consistency and correctness of probability and entity input via JSON.
- **Performance Benchmarking:** Comprehensive timing analysis for compilation and SHAP computation across different formula sizes.
- **Extensive Testing:** Comprehensive test suite for algorithm correctness, construction, and edge cases.
- **Easy Setup:** Automated environment setup and dependency installation.

---

## Project Structure

```
shap-sdd-project/
├── src/
│   ├── main.py                 # Complete execution pipeline
│   ├── shap/
│   │   └── compute_shap.py     # SHAP Algorithm 2 implementation
│   ├── sdd/
│   │   ├── sdd_utils.py        # CNF loading & SDD compilation
│   │   └── sdd_visualizer.py   # DOT visualization
│   └── utils/
│       └── helpers.py          # Input loaders, validation
├── tests/                      # Test suite and test data
│   ├── data/
│   │   ├── small/              # 2-variable test case
│   │   ├── medium/             # 4-variable test case
│   │   └── large/              # 6-variable test case
│   ├── test_compute_shap.py    # SHAP algorithm tests
│   ├── test_sdd_utils.py       # SDD construction tests
│   ├── test_helpers.py         # Validation tests
│   └── test_sdd_visualiser.py  # Visualization tests
├── benchmarks/
│   └── benchmark_shap.py       # Performance benchmarking suite
├── output/                     # Generated DOT/visualization files
├── requirements.txt            # Dependency specification
├── setup.sh                    # Automated setup
└── README.md
```

---

## Installation and Setup

### Prerequisites

- Python 3.8+ (_tested with 3.12_)
- pip
- [Graphviz](https://graphviz.org/) (optional, for visualizations)

### Quickstart

```bash
git clone <repository-url>
cd shap-sdd-project
chmod +x setup.sh
./setup.sh
```

This setup script will:
- Create a Python virtual environment
- Install all required dependencies (PySDD, NumPy, pytest, etc.)
- Run basic tests and validate modules
- Verify PySDD and SHAP module imports

**Manual Setup (Alternative):**

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## Usage

### Command-Line Interface

Activate the virtual environment (if not already active):

```bash
source venv/bin/activate
```

Process a CNF with SHAP analysis:

```bash
python src/main.py path/to/formula.cnf \
    --marginals path/to/product.json \
    --entity path/to/entity.json
```

#### JSON Formats

- **Marginals (`product.json`):**
  ```json
  {
    "x1": 0.20,
    "x2": 0.80,
    "x3": 0.50,
    "x4": 0.10
  }
  ```
- **Entity (`entity.json`):**
  ```json
  {
    "x1": 1,
    "x2": 0,
    "x3": 1,
    "x4": 0
  }
  ```

#### Example Run with Test Data

```bash
python src/main.py tests/data/test.cnf \
    --marginals tests/data/product.json \
    --entity tests/data/entity.json
```

Sample output:
```
✓ JSON validation passed
CNF file: tests/data/test.cnf
Marginals: {'x1': 0.2, 'x2': 0.8, 'x3': 0.5, 'x4': 0.1}
Entity: {'x1': 1, 'x2': 0, 'x3': 1, 'x4': 0}

SHAP Scores:
  x1: 0.213333
  x2: 0.123333
  x3: 0.156667
  x4: 0.010667
```

---

### Programmatic API

High-level usage:

```python
from src.shap.compute_shap import compute_shap_scores
from src.sdd.sdd_utils import load_cnf, construct_sdd
from src.utils.helpers import load_and_validate_json

# Load JSON-formatted marginals and entity
marginals, entity = load_and_validate_json("tests/data/product.json", "tests/data/entity.json")

# Compile SDD from CNF
cnf_formula = load_cnf("tests/data/test.cnf")
sdd = construct_sdd(cnf_formula)

# Compute SHAP scores
shap_scores = compute_shap_scores(sdd, marginals, entity)
print(shap_scores)
```

**Low-Level Usage with Variable IDs:**

```python
from src.shap.compute_shap import compute_shap_algorithm
from pysdd.sdd import SddManager

# Create SDD manually
manager = SddManager.from_cnf_string("p cnf 2 1\n1 2 0\n", vtree_type=b"right")[0]
sdd = manager.read_sdd_file("circuit.sdd")

# Define marginals and entity by variable ID
p = {1: 0.3, 2: 0.7}  # Variable IDs → marginal probabilities
e = {1: 1, 2: 0}      # Variable IDs → entity values

# Compute SHAP
shap_scores = compute_shap_algorithm(sdd, p, e)
print(shap_scores)  # {1: score1, 2: score2}

---

## Testing
### Running All Tests

Activate the environment first:
```bash
source venv/bin/activate
```

Run complete test suite (22 tests):
```bash
python -m pytest tests/ -v
```

**Expected Output:**
```
tests/test_compute_shap.py::TestComputeShap::test_compute_shap_scores PASSED
tests/test_compute_shap.py::TestComputeShap::test_complex_formula_shap PASSED
tests/test_compute_shap.py::TestComputeShap::test_algorithm2_with_fixed_combinatorics PASSED
tests/test_compute_shap.py::TestComputeShap::test_with_cnf_file PASSED
tests/test_helpers.py::TestHelpers::test_parse_cnf_file PASSED
tests/test_helpers.py::TestHelpers::test_validate_json_marginals_valid PASSED
... (16 more tests)
tests/test_sdd_utils.py::TestSddUtils::test_load_cnf PASSED
tests/test_sdd_utils.py::TestSddUtils::test_construct_sdd PASSED
tests/test_sdd_visualiser.py::TestSddVisualizer::test_sdd_to_dot PASSED

===================== 22 passed in 2.34s =====================
```

### Running Specific Test Modules

```bash
# Test SHAP algorithm only
python -m pytest tests/test_compute_shap.py -v

# Test validation utilities only
python -m pytest tests/test_helpers.py -v

# Test with coverage report
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

### Test Categories

| Module | Tests | Coverage |
|--------|-------|----------|
| **test_compute_shap.py** | 4 | SHAP algorithm correctness, symmetry, efficiency |
| **test_helpers.py** | 16 | JSON validation, CNF parsing, compatibility checks |
| **test_sdd_utils.py** | 2 | SDD construction, CNF loading |
| **test_sdd_visualiser.py** | 1 | DOT file generation |

---

### Benchmark Test Cases

The benchmark suite includes three test cases with increasing complexity:

| Test Case | Variables | Clauses | Description |
|-----------|-----------|---------|-------------|
| **Small** | 2 | 1 | Simple disjunction: (A ∨ B) |
| **Medium** | 4 | 2 | Independent clauses: (A ∨ B) ∧ (C ∨ D) |
| **Large** | 6 | 8 | Satisfiable 3-SAT problem |

### Sample Benchmark Output

```
============================================================
TEST CASE: Small (2 vars, 1 clause) - Symmetric
============================================================

Benchmarking: tests/data/small/formula.cnf
Number of runs: 20
------------------------------------------------------------
Variables: 2
SDD Size: 5 nodes

Load Time:
  Mean:   0.82 ms
  Median: 0.79 ms
  StdDev: 0.15 ms

Compile Time:
  Mean:   2.34 ms
  Median: 2.28 ms
  StdDev: 0.31 ms

SHAP Computation Time:
  Mean:   0.67 ms
  Median: 0.64 ms
  StdDev: 0.12 ms

Total Time:
  Mean:   3.83 ms
  Median: 3.76 ms
  StdDev: 0.42 ms

Time Breakdown:
  Load/Validation: 21.4%
  SDD Compilation: 61.1%
  SHAP Computation: 17.5%

============================================================
SUMMARY TABLE
============================================================
Test Case                                     Vars   SDD      Compile    SHAP       Total     
--------------------------------------------- ------ -------- ---------- ---------- ----------
Small (2 vars, 1 clause)                      2      5        2.34       0.67       3.83      
Medium (4 vars, 2 clauses)                    4      14       3.12       1.45       5.39      
Large (6 vars, 8 clauses)                     6      47       8.71       4.23       13.76     
```

### Benchmark Metrics

The benchmark measures:

1. **Load Time:** JSON validation and CNF parsing
2. **Compile Time:** SDD construction from CNF (typically 60-70% of total)
3. **SHAP Computation Time:** Algorithm 2 execution (typically 20-30% of total)
4. **Total Time:** End-to-end pipeline
5. **SDD Size:** Number of nodes in compiled circuit

### Performance Characteristics

**Complexity:**
- **Time:** O(n × |SDD| × d²) where n = variables, |SDD| = circuit size, d = max gate degree
- **Space:** O(|SDD| × n) for γ/δ arrays

**Typical Performance (on M1 Mac, Python 3.12):**
- Small formulas (2-4 vars): 3-5 ms total
- Medium formulas (4-6 vars): 5-15 ms total
- Compilation dominates runtime (60-70%)
- SHAP computation scales linearly with variables

### Custom Benchmarks

To benchmark your own formulas:

```python
from benchmarks.benchmark_shap import run_benchmark

results = run_benchmark(
    cnf_file="path/to/formula.cnf",
    marginals_file="path/to/product.json",
    entity_file="path/to/entity.json",
    num_runs=20
)

# Results include timing statistics and SDD metrics
print(f"Average SHAP time: {results[0]['shap_time'] * 1000:.2f} ms")
print(f"SDD size: {results[0]['sdd_size']} nodes")
```

---

## Visualization

### Generating Visualizations

DOT files are automatically generated to the `output/` folder during tests. To manually generate:

```python
from src.sdd.sdd_visualizer import sdd_to_dot

# Assuming 'sdd' is your compiled SDD
litnamemap = {1: "A", 2: "B", -1: "¬A", -2: "¬B"}
dot_content = sdd_to_dot(sdd, litnamemap=litnamemap)

with open("output/my_sdd.dot", "w") as f:
    f.write(dot_content)
```

### Rendering DOT Files

Convert DOT files to images using Graphviz:

```bash
# PNG format
dot -Tpng output/sdd_formula.dot -o output/sdd_formula.png

# SVG format (scalable)
dot -Tsvg output/sdd_formula.dot -o output/sdd_formula.svg

# PDF format
dot -Tpdf output/sdd_formula.dot -o output/sdd_formula.pdf
```

**View images:**
```bash
# macOS
open output/sdd_formula.png

# Linux
xdg-open output/sdd_formula.png

# Windows
start output/sdd_formula.png
```

## Supported Formats

### CNF (DIMACS Format)

Standard DIMACS CNF format with comments and problem line:

```cnf
c This is a comment
c Formula: (A ∨ B) ∧ (C ∨ D)
p cnf 4 2
1 2 0
3 4 0
```

**Format Rules:**
- Comments start with `c`
- Problem line: `p cnf <num_vars> <num_clauses>`
- Each clause ends with `0`
- Variables numbered 1, 2, 3, ...
- Negation indicated by negative sign: `-1` = ¬x₁

### JSON (Marginals and Entity)

**Variable Naming:** Must use format `"x1"`, `"x2"`, `"x3"`, etc.

**Marginals Constraints:**
- Probabilities must be in range [0, 1]
- Must be numeric (int or float)

**Entity Constraints:**
- Values must be binary: 0 or 1
- Must be integers

**Validation:** Both files must have identical variable sets.

---

# Troubleshooting

### Installation Issues

**PySDD failing to install?**

1. Upgrade build tools:
   ```bash
   pip install --upgrade setuptools wheel pip
   ```

2. Install PySDD separately:
   ```bash
   pip install pysdd
   ```

3. If still failing, check Python version:
   ```bash
   python --version  # Should be 3.8+
   ```

### Runtime Errors

**Import errors?**

```bash
# Activate virtual environment
source venv/bin/activate

# Verify Python path
python -c "import sys; print(sys.path)"

# Test imports
python -c "from pysdd.sdd import SddManager; print('PySDD works!')"
python -c "from src.shap.compute_shap import compute_shap_scores; print('SHAP works!')"
```

**Test failures?**

```bash
# Clear pytest cache
python -m pytest --cache-clear

# Run with verbose output
python -m pytest tests/ -vv

# Run single test for debugging
python -m pytest tests/test_compute_shap.py::TestComputeShap::test_compute_shap_scores -vv
```

**JSON validation errors?**

```bash
# Check file format
cat tests/data/medium/product.json | python -m json.tool

# Verify variable names
python -c "
import json
with open('tests/data/medium/product.json') as f:
    data = json.load(f)
    print('Variables:', list(data.keys()))
    print('Valid format:', all(k.startswith('x') for k in data.keys()))
"
```

### Debugging

Enable detailed logging:

```bash
# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Enable debug logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from shap.compute_shap import compute_shap_scores
# Your code here
"
```

**Debug specific components:**

```python
# Uncomment logging lines in source files:
# src/shap/compute_shap.py - lines 5, 52, 174
# src/sdd/sdd_utils.py - lines 5, 22, 33

import logging
logging.basicConfig(level=logging.DEBUG)

# Then run your code
```
---

## References

### Core Libraries

- **PySDD:** Python package for compiling and manipulating Sentential Decision Diagrams  
  Repository: [ML-KULeuven/PySDD](https://github.com/ML-KULeuven/pysdd)  
  Documentation: [PySDD Docs](https://pysdd.readthedocs.io/)

### Research Papers

- **Algorithm Source:**  
  Marcelo Arenas, Pablo Barceló, Leopoldo Bertossi, Mikaël Monet  
  *"On the Complexity of SHAP-Score-Based Explanations: Tractability via Knowledge Compilation and Non-Approximability Results"*  
  Journal of Machine Learning Research, 24:1–58, 2023  
  [https://www.jmlr.org/papers/v24/21-0389.html](https://www.jmlr.org/papers/v24/21-0389.html)

- **SDD Theory:**  
  Adnan Darwiche  
  *"SDD: A New Canonical Representation of Propositional Knowledge Bases"*  
  IJCAI 2011  
  [http://reasoning.cs.ucla.edu/sdd/](http://reasoning.cs.ucla.edu/sdd/)

---