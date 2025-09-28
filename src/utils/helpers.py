def parse_cnf_file(file_path):
    """Parses a CNF DIMACS file and returns a list of clauses."""
    clauses = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('c') or line.startswith('p'):
                continue
            clause = list(map(int, line.strip().split()))[:-1]  # Exclude the trailing 0
            clauses.append(clause)
    return clauses

def validate_clauses(clauses):
    """Validates the clauses to ensure they are in the correct format."""
    for clause in clauses:
        if not isinstance(clause, list) or not all(isinstance(lit, int) for lit in clause):
            raise ValueError("Invalid clause format: {}".format(clause))



