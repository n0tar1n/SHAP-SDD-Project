import os
from pysdd.sdd import SddManager, Vtree, SddNode
# import logging

# logging.basicConfig(level=logging.DEBUG)

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
    if not isinstance(cnf_formula, str) or not cnf_formula.strip():
        raise ValueError("construct_sdd expects a non-empty DIMACS CNF string")

    # Compile the CNF formula into an SDD
    # logging.debug("Compiling CNF to SDD...")
    
    result = SddManager.from_cnf_string(cnf_formula, vtree_type=b"right")

    # PySDD returns (manager, sdd) tuple
    if isinstance(result, tuple) and len(result) == 2:
        manager, sdd = result
    else:
        raise TypeError(f"Unexpected return type from SddManager.from_cnf_string: {type(result)}")

    if not isinstance(sdd, SddNode):
        raise TypeError(f"Invalid SDD type: {type(sdd)}")

    # logging.debug("SDD construction complete.")
    return sdd
