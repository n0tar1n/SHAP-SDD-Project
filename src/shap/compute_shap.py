from pysdd.sdd import WmcManager, SddNode
from collections import defaultdict
from math import factorial, comb
# import logging

# logging.basicConfig(level=logging.DEBUG)

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
        # logging.debug(f"Computing SHAP for variable {x}")
        
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
                # Parent vars excluding x
                Vg = (var_of[g] - {x})
                L = len(Vg)

                # Init parent arrays
                gamma[g] = [0.0] * (L + 1)
                delta[g] = [0.0] * (L + 1)

                # ---- Phase 1: AND (prime ∧ sub) ----
                per_child = []  # (child_gamma, child_delta, child_vars)
                for prime, sub in g.elements():
                    Vp = (var_of[prime] - {x})
                    Vs = (var_of[sub] - {x})
                    Vc = Vp | Vs
                    Lp, Ls = len(Vp), len(Vs)
                    child_len = len(Vc)

                    child_gamma = [0.0] * (child_len + 1)
                    child_delta = [0.0] * (child_len + 1)

                    # decomposable AND, NO combinatorial weights
                    for ell_child in range(child_len + 1):
                        lo = max(0, ell_child - Ls)
                        hi = min(ell_child, Lp)
                        gsum = 0.0
                        dsum = 0.0
                        for ell_p in range(lo, hi + 1):
                            ell_s = ell_child - ell_p
                            if 0 <= ell_s <= Ls:
                                gsum += gamma[prime][ell_p] * gamma[sub][ell_s]
                                dsum += delta[prime][ell_p] * delta[sub][ell_s]
                        child_gamma[ell_child] = gsum
                        child_delta[ell_child] = dsum

                    per_child.append((child_gamma, child_delta, Vc))

                # ---- Phase 2: OR over elements ----
                for child_gamma, child_delta, Vc in per_child:
                    missing = len(Vg - Vc)
                    max_child = len(Vc)
                    for ell_parent in range(L + 1):
                        upper = min(ell_parent, max_child)
                        acc_g = 0.0
                        acc_d = 0.0
                        for ell_child in range(upper + 1):
                            # virtual smoothing binomial factor
                            try:
                                w = comb(missing, ell_parent - ell_child)
                                acc_g += child_gamma[ell_child] * w
                                acc_d += child_delta[ell_child] * w
                            except (ValueError, OverflowError):
                                # Handle edge cases in combinatorial computation
                                
                                # logging.warning(f"Combinatorial computation failed for missing={missing}, ell_parent={ell_parent}, ell_child={ell_child}")
                                continue
                        gamma[g][ell_parent] += acc_g
                        delta[g][ell_parent] += acc_d
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
            
            # logging.debug(f"Variable {x}, k={k}, weight={weight}, gamma={gamma[gout][k]}, delta={delta[gout][k]}, term={term}")
        
        shap_scores[x] = shap_x
        # logging.debug(f"SHAP score for variable {x}: {shap_x}")
    
    return shap_scores

def compute_shap_scores(sdd, marginals=None, entity=None):
    """
    Compute SHAP scores for an SDD with given marginals and entity values.
    
    Args:
        sdd: SddNode root of the compiled circuit
        marginals: dict mapping variable names (e.g., "x1") to marginal probabilities
        entity: dict mapping variable names (e.g., "x1") to entity values (0 or 1)
    
    Returns:
        dict mapping variable names to SHAP scores
    """
    if sdd is None:
        raise ValueError("The SDD is None. Cannot compute SHAP scores.")
    
    # Extract variables from SDD
    variables = list(sdd.manager.vars)
    
    # Build mapping from variable ID to variable name
    var_id_to_name = {abs(var.literal): f"x{abs(var.literal)}" for var in variables}
    
    # If marginals or entity not provided, use defaults (backward compatibility)
    if marginals is None:
        # logging.warning("No marginals provided, using uniform probabilities (0.5)")
        marginals = {var_id_to_name[abs(var.literal)]: 0.5 for var in variables}
    
    if entity is None:
        # logging.warning("No entity provided, using all variables set to 1")
        entity = {var_id_to_name[abs(var.literal)]: 1 for var in variables}
    
    # Convert to IDs 
    p = {}
    e = {}
    for var in variables:
        var_id = abs(var.literal)
        var_name = var_id_to_name[var_id]  # Use existing mapping
        
        p[var_id] = marginals.get(var_name, 0.5)
        e[var_id] = entity.get(var_name, 1)
    
    # logging.debug(f"Computing SHAP with marginals: {marginals}")
    # logging.debug(f"Computing SHAP with entity: {entity}")
    
    # Call Algorithm 2 implementation
    shap_scores_by_id = compute_shap_algorithm(sdd, p, e)
    
    # Convert back to variable names for output
    result = {var_id_to_name[var_id]: score 
              for var_id, score in shap_scores_by_id.items()}
    
    return result