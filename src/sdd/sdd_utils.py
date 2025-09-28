from pysdd.sdd import SddManager, Vtree
import logging

logging.basicConfig(level=logging.DEBUG)

def load_cnf(cnf_file):
    """
    Loads a CNF DIMACS file and returns its content as a string.
    """
    with open(cnf_file, 'r') as file:
        return file.read()

def construct_sdd(cnf_formula):
    """
    Compiles the CNF formula into an SDD using a right-linear vtree.
    """
    # Parse the CNF header to get number of variables
    header_found = False
    num_vars = 0
    
    for line in cnf_formula.splitlines():
        line = line.strip()
        if line.startswith("p cnf"):
            header_found = True
            parts = line.split()
            num_vars = int(parts[2])
            num_clauses = int(parts[3])
            logging.debug(f"CNF header: {num_vars} variables, {num_clauses} clauses")
            break
        elif line.startswith("c") or line == "":
            # Skip comments and empty lines
            continue
    
    if not header_found:
        raise ValueError("Invalid CNF formula. No 'p cnf' header found.")

    if num_vars == 0:
        raise ValueError("No variables found in CNF formula.")

    # Create a right-linear vtree 
    logging.debug(f"Creating right-linear vtree for {num_vars} variables")
    vtree = Vtree(var_count=num_vars, vtree_type="right")

    # Create an SDD manager using the vtree
    sdd_manager = SddManager.from_vtree(vtree)

    # Compile the CNF formula into an SDD
    logging.debug("Compiling CNF to SDD...")
    
    # The from_cnf_string method modifies the manager and returns it
    # We need to get the actual SDD from the manager after compilation
    result = sdd_manager.from_cnf_string(cnf_formula)
    
    # Check if result is a tuple (manager, sdd) or just manager
    if isinstance(result, tuple):
        manager, sdd = result
        logging.debug(f"Got tuple result: manager={type(manager)}, sdd={type(sdd)}")
    else:
        # Result is the manager, we need to get the SDD from it
        manager = result
        # The compiled SDD should be accessible through the manager
        # Try to get the root SDD node
        try:
            # Method 1: Check if manager has a root or compiled SDD
            if hasattr(manager, 'root') and manager.root is not None:
                sdd = manager.root
                logging.debug(f"Got SDD from manager.root: {sdd}")
            # Method 2: Try to get the last compiled formula
            elif hasattr(manager, 'true'):
                # Build a simple SDD to verify the manager works
                sdd = manager.true()  # Get the TRUE constant as a test
                logging.debug(f"Manager is working, got TRUE constant: {sdd}")
                
                # Reconstruct the formula from CNF
                # Parse clauses and build SDD manually
                clauses = []
                for line in cnf_formula.splitlines():
                    line = line.strip()
                    if line.startswith('c') or line.startswith('p') or line == '':
                        continue
                    clause = [int(x) for x in line.split() if int(x) != 0]
                    if clause:  # Only add non-empty clauses
                        clauses.append(clause)
                
                logging.debug(f"Parsed {len(clauses)} clauses: {clauses}")
                
                # Build SDD from clauses
                if not clauses:
                    sdd = manager.true()
                else:
                    # Convert each clause to SDD (disjunction of literals)
                    clause_sdds = []
                    for clause in clauses:
                        if len(clause) == 1:
                            # Single literal
                            lit = clause[0]
                            if lit > 0:
                                lit_sdd = manager.literal(lit)
                            else:
                                lit_sdd = -manager.literal(-lit)
                        else:
                            # Multiple literals - OR them together
                            lit_sdds = []
                            for lit in clause:
                                if lit > 0:
                                    lit_sdds.append(manager.literal(lit))
                                else:
                                    lit_sdds.append(-manager.literal(-lit))
                            
                            # OR all literals in the clause
                            lit_sdd = lit_sdds[0]
                            for other in lit_sdds[1:]:
                                lit_sdd = lit_sdd | other
                        
                        clause_sdds.append(lit_sdd)
                    
                    # AND all clauses together
                    sdd = clause_sdds[0]
                    for other in clause_sdds[1:]:
                        sdd = sdd & other
                
                logging.debug(f"Built SDD from clauses: {sdd}")
            else:
                raise ValueError("Cannot extract SDD from manager")
                
        except Exception as e:
            logging.error(f"Error extracting SDD from manager: {e}")
            raise ValueError(f"Failed to get SDD from manager: {e}")
    
    # Verify we have a valid SDD node
    if not hasattr(sdd, 'manager'):
        raise ValueError(f"Invalid SDD node returned. Type: {type(sdd)}")
    
    logging.debug(f"SDD construction complete. Root node: {sdd}")
    logging.debug(f"SDD type: {type(sdd)}")
    return sdd
