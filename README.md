# SHAP-SDD Project

## Overview

The **SHAP-SDD Project** implements **Algorithm 2** from the SDD research paper for computing SHAP (SHapley Additive exPlanations) scores on **Sentential Decision Diagrams (SDDs)**.


## Project Structure

shap-sdd-project/
├── src/                          # Source code
│   ├── main.py                   # Main entry point - complete pipeline
│   ├── shap/
│   │   ├── __init__.py
│   │   └── compute_shap.py       # Algorithm 2 implementation
│   ├── sdd/
│   │   ├── __init__.py
│   │   ├── sdd_utils.py          # CNF loading & SDD construction
│   │   └── sdd_visualizer.py     # DOT file generation for visualization
│   └── utils/
│       ├── __init__.py
│       └── helpers.py            # Utility functions
├── tests/                        # Comprehensive test suite
│   ├── data/                     # Test CNF files
│   ├── test_compute_shap.py      # SHAP algorithm tests
│   ├── test_sdd_utils.py         # SDD construction tests
│   ├── test_sdd_visualiser.py    # Visualization tests
│   └── test_helpers.py           # Helper function tests
├── output/                       # Generated files (DOT, visualizations)
├── requirements.txt              # Python dependencies
├── setup.sh                      # Automated setup script
├── .gitignore                    # Git ignore rules
└── README.md


## Algorithm Implementation

### Core Features

1. **Algorithm Implementation** (`src/shap/compute_shap.py`):
   - Bottom-up computation with γ (gamma) and δ (delta) arrays
   - Proper handling of constant gates, variable gates, and decision gates
   - Combinatorial weighting for OR-gate variable overlaps
   - SHAP score aggregation using exact mathematical formula

2. **Right-Linear Vtree Construction** (`src/sdd/sdd_utils.py`):
   - Enforces right-linear vtree structure 
   - Compiles CNF DIMACS files into SDDs with proper gate structure
   - Handles both automatic compilation and manual construction fallback

3. **SDD Visualization** (`src/sdd/sdd_visualizer.py`):
   - Generates DOT files for Graphviz visualization
   - Represents SDD structure with proper gate labeling
   - Essential for validating SDD construction correctness

4. **JSON Input Support** (`src/utils/helpers.py`):
   - Load and validate marginal probability distributions
   - Load and validate entity value assignments
   - Verify variable name consistency between inputs
   - Comprehensive error messages for invalid inputs
   - Helper function `load_and_validate_json()` for streamlined loading

## Setup Instructions

### Prerequisites
- Python 3.8+ (tested with Python 3.12)
- pip package manager
- Graphviz (optional, for visualization)

### Quick Setup (Recommended)

1. **Clone the repository:**
   bash
   git clone <repository-url>
   cd shap-sdd-project
   

2. **Run the automated setup:**
   bash
   chmod +x setup.sh
   ./setup.sh
   

   This script will:
   - Create a Python virtual environment
   - Install all required dependencies
   - Test the installation
   - Verify PySDD and SHAP modules work correctly




### Dependencies

The project requires these key packages:
- pysdd>=1.0.5
- Core SDD library (REQUIRED)
- `numpy>=1.21.0` - Scientific computing
- `pytest>=7.0.0` - Testing framework
- Additional packages for visualization and development (see requirements.txt)

## Usage

### Basic Usage with JSON Files

#### Activate virtual environment (if not already active)
source venv/bin/activate

#### Run with a CNF file and JSON inputs
python src/main.py path/to/formula.cnf \
    --marginals path/to/product.json \
    --entity path/to/entity.json

### JSON Input Format

#### Product Distribution (marginals) - product.json:

{
  "x1": 0.20,
  "x2": 0.80,
  "x3": 0.50,
  "x4": 0.10
}

#### Input Instance (entity) - entity.json:

{
  "x1": 1,
  "x2": 0,
  "x3": 1,
  "x4": 0
}

### Example with Test Data

#### Run with provided test files
python src/main.py tests/data/test.cnf \
    --marginals tests/data/product.json \
    --entity tests/data/entity.json

#### Expected Output

✓ JSON validation passed
CNF file: tests/data/test.cnf
Marginals: {'x1': 0.2, 'x2': 0.8, 'x3': 0.5, 'x4': 0.1}
Entity: {'x1': 1, 'x2': 0, 'x3': 1, 'x4': 0}

SHAP Scores:
  x1: 0.213333
  x2: 0.123333
  x3: 0.156667
  x4: 0.010667


### Advanced Usage - Programmatic API

For programmatic use with custom marginal probabilities and entity values:

```python
from src.shap.compute_shap import compute_shap_scores, compute_shap_algorithm
from src.sdd.sdd_utils import load_cnf, construct_sdd
from src.utils.helpers import load_and_validate_json

# Method 1: High-level API with JSON files
marginals, entity = load_and_validate_json(
    "tests/data/product.json",
    "tests/data/entity.json"
)

# Load and construct SDD
cnf_formula = load_cnf("tests/data/test.cnf")
sdd = construct_sdd(cnf_formula)

# Compute SHAP scores (returns dict with variable names as keys)
shap_scores = compute_shap_scores(sdd, marginals, entity)
print(f"SHAP scores: {shap_scores}")

# Method 2: Low-level API with variable IDs
p = {1: 0.6, 2: 0.7, 3: 0.4, 4: 0.8}  # Marginal probabilities
e = {1: 1, 2: 0, 3: 1, 4: 1}           # Entity values
shap_scores_by_id = compute_shap_algorithm(sdd, p, e)
print(f"SHAP scores by ID: {shap_scores_by_id}")

## Testing

### Run All Tests
# Activate environment
source venv/bin/activate

# Run complete test suite
python -m pytest tests/ -v

# Run specific test categories
## SHAP algorithm tests (4 tests)
python -m pytest tests/test_compute_shap.py -v

## SDD construction tests (2 tests)
python -m pytest tests/test_sdd_utils.py -v

## JSON validation tests (9 tests)
python -m pytest tests/test_helpers.py -v

## Visualization tests (1 test)
python -m pytest tests/test_sdd_visualiser.py -v


### Test Coverage

The test suite includes:
- **Algorithm validation** with known formulas
- **SDD construction** with right-linear vtrees
- **Visualization generation** and DOT file creation
- **Edge cases** and error handling
- **Integration tests** with CNF files

## Visualization

### Generate SDD Visualizations

The pipeline automatically generates DOT files in the output directory:

# Convert DOT to PNG (requires Graphviz)
dot -Tpng output/sdd.dot -o output/sdd.png

# Convert DOT to SVG
dot -Tsvg output/sdd.dot -o output/sdd.svg

# View the visualization
open output/sdd.png  # macOS
xdg-open output/sdd.png  # Linux


### Formula Requirements

Your CNF DIMACS files should:
- Use standard DIMACS format
- Start with comment lines (c ...)
- Include problem line: `p cnf <num_vars> <num_clauses>`
- End clauses with `0`


## Troubleshooting

### Common Issues

1. **PySDD Installation Failed**:
   # Try upgrading build tools
   pip install --upgrade setuptools wheel
   pip install pysdd
   

2. **Import Errors**:
   # Ensure virtual environment is activated
   source venv/bin/activate
   # Verify Python path
   python -c "import sys; print(sys.path)"
   

3. **Test Failures**:
   # Clear pytest cache
   python -m pytest --cache-clear
   # Run individual tests for debugging
   python -m pytest tests/test_compute_shap.py::TestComputeShap::test_algorithm2_with_fixed_combinatorics -v
   

### Debug Mode

For detailed algorithm tracing:
# Enable debug logging
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python src/main.py your_formula.cnf




