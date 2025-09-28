from pysdd.sdd import WmcManager, SddNode
from collections import defaultdict
from math import factorial, comb
import logging

logging.basicConfig(level=logging.DEBUG)

def get_topological_order(sdd):
    """Returns gates in bottom-up order (leaves first)"""
    # DFS traversal to ensure children are processed before parents
    visited = set()
    topo_order = []
    
    def dfs(node):
        if node.id in visited:
            return
        visited.add(node.id)
        
        # Visit children first (for decomposition nodes)
        if node.is_decision():
            for prime, sub in node.elements():
                dfs(prime)
                dfs(sub)
        
        topo_order.append(node)
    
    dfs(sdd)
    return topo_order

def is_constant_gate(node):
    # Check if node is a constant (True/False)
    return node.is_true() or node.is_false()

def is_variable_gate(node):
    # Check if node is a literal
    return node.is_literal()

def is_negation_gate(node):
    # Check if node represents negation (negative literal)
    return node.is_literal() and node.literal < 0

def constant_value(node):
    # Get constant value (0 or 1)
    return 1 if node.is_true() else 0

def variable_of(node):
    # Get variable ID from literal node
    return abs(node.literal)

def compute_shap_algorithm(sdd, p, e):
    """    
    Args:
        sdd: root SddNode of a deterministic, decomposable Boolean circuit
        p: dict mapping variable id -> marginal probability p(x)
        e: dict mapping variable id -> entity value (0 or 1)
    
    Returns:
        dict var -> SHAP(C, e, var)
    """
    
    # 1. Compute var(g): set of variables that g depends on
    var_of = {}
    topo_order = get_topological_order(sdd)
    
    for g in topo_order:
        if is_constant_gate(g):
            var_of[g] = set()
        elif is_variable_gate(g):
            var_of[g] = {variable_of(g)}
        elif g.is_decision():
            # For SDD decision nodes, collect variables from all elements
            all_vars = set()
            for prime, sub in g.elements():
                all_vars.update(var_of.get(prime, set()))
                all_vars.update(var_of.get(sub, set()))
            var_of[g] = all_vars
        else:
            raise NotImplementedError(f"Unknown gate type for node {g.id}")
    
    # 2. Compute SHAP scores for each variable
    shap_scores = {}
    X = list(p.keys())
    n = len(X)
    
    for x in X:
        logging.debug(f"Computing SHAP for variable {x}")
        
        # Initialize gamma and delta arrays for each gate
        gamma = {}
        delta = {}
        
        # Bottom-up computation
        for g in topo_order:
            Vg = var_of[g]
            Vg_without_x = Vg - {x}
            max_ell = len(Vg_without_x)
            
            # Initialize arrays
            gamma[g] = [0.0] * (max_ell + 1)
            delta[g] = [0.0] * (max_ell + 1)
            
            if is_constant_gate(g):
                a = constant_value(g)       # 0 (False) or 1 (True)
                for ell in range(max_ell + 1):
                    gamma[g][ell] = a
                    delta[g][ell] = a
                    
            elif is_variable_gate(g):
                y = variable_of(g)
                if y == x:      # This gate represents variable x (or ¬x)
                    # var(g) = {x}, so max_ell = 0
                    if is_negation_gate(g):
                        gamma[g][0] = 0  # ¬x when x=1
                        delta[g][0] = 1  # ¬x when x=0
                    else:
                        gamma[g][0] = 1  # x when x=1
                        delta[g][0] = 0  # x when x=0
                else:
                    # var(g) = {y}, y ≠ x, so max_ell = 0
                    if is_negation_gate(g):
                        gamma[g][0] = 1 - p[y]  # ¬y
                        delta[g][0] = 1 - e[y]  # ¬y under entity
                    else:
                        gamma[g][0] = p[y]      # y marginal probability
                        delta[g][0] = e[y]      # y under entity
                        
            elif g.is_decision():
                # SDD decision node - represents disjunction of conjunctions
                for ell in range(max_ell + 1):
                    val_gamma = 0.0
                    val_delta = 0.0
                    
                    # Each element (prime, sub) represents prime ∧ sub
                    for prime, sub in g.elements():
                        V_prime = var_of[prime] - {x}
                        V_sub = var_of[sub] - {x}
                        max_prime = len(V_prime)
                        max_sub = len(V_sub)
                        
                        # Fixed combinatorial weighting logic
                        # Compute overlaps carefully
                        V_prime_only = V_prime - V_sub
                        V_sub_only = V_sub - V_prime
                        V_common = V_prime & V_sub
                        
                        count_prime_only = len(V_prime_only)
                        count_sub_only = len(V_sub_only)
                        count_common = len(V_common)
                        
                        # Clarified ℓ bounds in loops
                        for ell_prime in range(0, min(ell, max_prime) + 1):
                            ell_sub = ell - ell_prime
                            if ell_sub > max_sub or ell_sub < 0:
                                continue
                            
                            # Ensure no negative values and correct counts
                            # We need to distribute ell variables between prime and sub
                            # considering their overlap
                            
                            # For AND gate (prime ∧ sub), we need both to be satisfied
                            # The combinatorial weight accounts for how many ways we can
                            # choose variables from the exclusive sets
                            
                            if (0 <= ell_sub <= count_sub_only and 
                                0 <= ell_prime <= count_prime_only):
                                
                                try:
                                    # Apply combinatorial weighting as per Algorithm 2
                                    weight = comb(count_sub_only, ell_sub) * comb(count_prime_only, ell_prime)
                                    
                                    # AND gate computation for this element
                                    val_gamma += weight * gamma[prime][ell_prime] * gamma[sub][ell_sub]
                                    val_delta += weight * delta[prime][ell_prime] * delta[sub][ell_sub]
                                    
                                except (ValueError, OverflowError):
                                    # Handle edge cases in combinatorial computation
                                    logging.warning(f"Combinatorial computation failed for ell_prime={ell_prime}, ell_sub={ell_sub}")
                                    continue
                    
                    gamma[g][ell] = val_gamma
                    delta[g][ell] = val_delta
            else:
                raise NotImplementedError(f"Gate type not handled for node {g.id}")
        
        # Compute SHAP score for variable x
        gout = sdd  # root node
        var_out = var_of[gout]
        max_out = len(var_out - {x})
        
        shap_x = 0.0
        for k in range(max_out + 1):
            # SHAP weight formula - fixed edge case for n=1
            if n == 1:
                weight = 1.0
            else:
                weight = factorial(k) * factorial(n - k - 1) / factorial(n)
            
            term = (e[x] - p[x]) * (gamma[gout][k] - delta[gout][k])
            shap_x += weight * term
            
            logging.debug(f"Variable {x}, k={k}, weight={weight}, gamma={gamma[gout][k]}, delta={delta[gout][k]}, term={term}")
        
        shap_scores[x] = shap_x
        logging.debug(f"SHAP score for variable {x}: {shap_x}")
    
    return shap_scores

def compute_shap_scores(sdd):
    """
    Wrapper function to maintain compatibility with existing tests
    """
    if sdd is None:
        raise ValueError("The SDD is None. Cannot compute SHAP scores.")
    
    # Extract variables from SDD
    variables = list(sdd.manager.vars)
    
    # Set uniform marginal probabilities and entity values for testing
    p = {abs(var.literal): 0.5 for var in variables}  # Uniform marginals
    e = {abs(var.literal): 1 for var in variables}    # All variables set to 1
    
    # Call Algorithm 2 implementation
    shap_scores = compute_shap_algorithm(sdd, p, e)
    
    # Convert back to SDD variable objects for compatibility
    result = {}
    for var in variables:
        var_id = abs(var.literal)
        if var_id in shap_scores:
            result[var] = shap_scores[var_id]
        
    return result