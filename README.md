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

### Basic Usage

# Activate virtual environment (if not already active)
source venv/bin/activate

# Run with a CNF DIMACS file
python src/main.py path/to/your/formula.cnf


### Example with Test Data

# Create a test CNF file
cat > test_formula.cnf << 'EOF'
c Test formula: (A ∧ B) ∨ (C ∧ D)
p cnf 4 4
1 2 0
3 4 0
-1 -2 3 4 0
-3 -4 1 2 0
EOF

# Run the pipeline
python src/main.py test_formula.cnf


### Expected Output

DEBUG:root:CNF header: 4 variables, 4 clauses
DEBUG:root:Creating right-linear vtree for 4 variables
DEBUG:root:Computing SHAP for variable 1
DEBUG:root:SHAP score for variable 1: -0.03125
DEBUG:root:Computing SHAP for variable 2
DEBUG:root:SHAP score for variable 2: -0.03125
DEBUG:root:Computing SHAP for variable 3
DEBUG:root:SHAP score for variable 3: -0.03125
DEBUG:root:Computing SHAP for variable 4
DEBUG:root:SHAP score for variable 4: -0.03125
SHAP Scores: {SddNode(name=1,id=3): -0.03125, SddNode(name=2,id=5): -0.03125, SddNode(name=3,id=7): -0.03125, SddNode(name=4,id=9): -0.03125}
SDD visualization saved to 'output/sdd.dot'.


### Advanced Usage

For custom marginal probabilities and entity values:

python
from src.shap.compute_shap import compute_shap_algorithm
from src.sdd.sdd_utils import load_cnf, construct_sdd

# Load and construct SDD
cnf_formula = load_cnf("your_formula.cnf")
sdd = construct_sdd(cnf_formula)

# Define custom parameters
p = {1: 0.6, 2: 0.7, 3: 0.4, 4: 0.8}  # Marginal probabilities
e = {1: 1, 2: 0, 3: 1, 4: 1}           # Entity values

# Compute SHAP scores with Algorithm 2
shap_scores = compute_shap_algorithm2(sdd, p, e)
print(f"SHAP scores: {shap_scores}")


## Testing

### Run All Tests
# Activate environment
source venv/bin/activate

# Run complete test suite
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_compute_shap.py -v     # SHAP algorithm tests
python -m pytest tests/test_sdd_utils.py -v       # SDD construction tests


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




