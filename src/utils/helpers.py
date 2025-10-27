def parse_cnf_file(file_path):
    """Parses a CNF DIMACS file and returns a list of clauses."""
    clauses = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('c') or line.startswith('p'):
                continue
            clause = list(map(int, line.strip().split()))[:-1]  # Exclude the trailing 0
            if clause:  # Skip empty lines
                clauses.append(clause)
    return clauses


def validate_clauses(clauses):
    """Validates the clauses to ensure they are in the correct format."""
    if not isinstance(clauses, list):
        raise ValueError("Clauses must be a list")
    
    for clause in clauses:
        if not isinstance(clause, list):
            raise ValueError(f"Invalid clause format: {clause}. Each clause must be a list.")
        if not all(isinstance(lit, int) for lit in clause):
            raise ValueError(f"Invalid clause format: {clause}. All literals must be integers.")


def validate_json_marginals(marginals):
    if not isinstance(marginals, dict):
        raise ValueError("Marginals must be a dictionary")
    
    if not marginals:
        raise ValueError("Marginals dictionary cannot be empty")
    
    for var_name, prob in marginals.items():
        # Validate variable name format
        if not isinstance(var_name, str):
            raise ValueError(f"Variable name must be a string, got {type(var_name)}")
        
        if not var_name.startswith('x'):
            raise ValueError(f"Variable name must start with 'x', got: {var_name}")
        
        try:
            var_idx = int(var_name[1:])
            if var_idx <= 0:
                raise ValueError(f"Variable index must be positive: {var_name}")
        except (ValueError, IndexError):
            raise ValueError(f"Invalid variable name format: {var_name}. Expected 'x1', 'x2', etc.")
        
        # Validate probability value
        if not isinstance(prob, (int, float)):
            raise ValueError(f"Marginal for {var_name} must be numeric, got {type(prob)}")
        
        if not (0 <= prob <= 1):
            raise ValueError(f"Marginal for {var_name} must be in [0,1], got {prob}")
    
    return True


def validate_json_entity(entity):
    if not isinstance(entity, dict):
        raise ValueError("Entity must be a dictionary")
    
    if not entity:
        raise ValueError("Entity dictionary cannot be empty")
    
    for var_name, value in entity.items():
        # Validate variable name format
        if not isinstance(var_name, str):
            raise ValueError(f"Variable name must be a string, got {type(var_name)}")
        
        if not var_name.startswith('x'):
            raise ValueError(f"Variable name must start with 'x', got: {var_name}")
        
        try:
            var_idx = int(var_name[1:])
            if var_idx <= 0:
                raise ValueError(f"Variable index must be positive: {var_name}")
        except (ValueError, IndexError):
            raise ValueError(f"Invalid variable name format: {var_name}. Expected 'x1', 'x2', etc.")
        
        # Validate entity value
        if not isinstance(value, int):
            raise ValueError(f"Entity value for {var_name} must be an integer, got {type(value)}")
        
        if value not in [0, 1]:
            raise ValueError(f"Entity value for {var_name} must be 0 or 1, got {value}")
    
    return True


def validate_json_compatibility(marginals, entity):
    marginal_vars = set(marginals.keys())
    entity_vars = set(entity.keys())
    
    if marginal_vars != entity_vars:
        missing_in_entity = marginal_vars - entity_vars
        missing_in_marginals = entity_vars - marginal_vars
        
        error_msg = "Variable mismatch between marginals and entity:"
        if missing_in_entity:
            error_msg += f"\n  In marginals but not in entity: {sorted(missing_in_entity)}"
        if missing_in_marginals:
            error_msg += f"\n  In entity but not in marginals: {sorted(missing_in_marginals)}"
        
        raise ValueError(error_msg)
    
    return True


def convert_to_sdd_format(clauses):
    if not clauses:
        return "p cnf 0 0\n"
    
    # Validate input
    validate_clauses(clauses)
    
    # Find the maximum variable index
    max_var = 0
    for clause in clauses:
        for lit in clause:
            max_var = max(max_var, abs(lit))
    
    num_vars = max_var
    num_clauses = len(clauses)
    
    # Build DIMACS format string
    lines = [f"p cnf {num_vars} {num_clauses}"]
    
    for clause in clauses:
        # Each clause ends with 0
        clause_str = " ".join(map(str, clause)) + " 0"
        lines.append(clause_str)
    
    return "\n".join(lines) + "\n"


def load_and_validate_json(marginals_path, entity_path):
    import json
    
    try:
        with open(marginals_path, 'r') as f:
            marginals = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Marginals file not found: {marginals_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in marginals file: {e}")
    
    # Load entity
    try:
        with open(entity_path, 'r') as f:
            entity = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Entity file not found: {entity_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in entity file: {e}")
    
    # Validate
    validate_json_marginals(marginals)
    validate_json_entity(entity)
    validate_json_compatibility(marginals, entity)
    
    return marginals, entity
