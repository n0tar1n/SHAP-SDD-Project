from pysdd.sdd import WmcManager, SddNode
from collections import defaultdict
from math import factorial, comb
import itertools
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
        sdd: root SddNode of a deterministic, decomposable Boolean circuit (OBDD-like)
        p: dict mapping variable id -> marginal probability p(x)
        e: dict mapping variable id -> entity value (0 or 1)
    
    Returns:
        dict var -> SHAP(C, e, var)
    """

    # 1. Compute var(g): set of variables that g depends on
    #    (Key by node.id to avoid wrapper-identity issues.)
    var_of = {}
    topo_order = get_topological_order(sdd)

    for g in topo_order:
        gid = g.id
        if is_constant_gate(g):
            var_of[gid] = set()
        elif is_variable_gate(g):
            var_of[gid] = {variable_of(g)}
        elif g.is_decision():
            # For SDD decision nodes, collect variables from all elements
            all_vars = set()
            for prime, sub in g.elements():
                all_vars.update(var_of[prime.id])
                all_vars.update(var_of[sub.id])
            var_of[gid] = all_vars
        else:
            raise NotImplementedError(f"Unknown gate type for node {g.id}")

    # 2. Compute SHAP scores for each variable
    X = list(p.keys())
    shap_scores = {x: 0.0 for x in X}

    gout = sdd  # root node
    gout_id = gout.id
    var_out = var_of[gout_id]

    # Reduced game size: only variables that actually appear in the circuit
    n = len(var_out)
    if n == 0:
        return shap_scores

    # Only compute SHAP for variables that are in the circuit;
    # variables in X but not in Var(circuit) are dummies => SHAP is exactly 0.
    X_in_circuit = [x for x in X if x in var_out]

    for x in X_in_circuit:
        gamma = {}
        delta = {}

        # Bottom-up computation
        for g in topo_order:
            gid = g.id
            Vg = var_of[gid]
            Vg_without_x = Vg - {x}
            max_ell = len(Vg_without_x)

            # Initialize arrays
            gamma[gid] = [0.0] * (max_ell + 1)
            delta[gid] = [0.0] * (max_ell + 1)

            if is_constant_gate(g):
                a = constant_value(g)       # 0 (False) or 1 (True)
                for ell in range(max_ell + 1):
                    gamma[gid][ell] = a
                    delta[gid][ell] = a

            elif is_variable_gate(g):
                y = variable_of(g)

                if y == x:      # This gate represents variable x (or ¬x)
                    # var(g) = {x} => max_ell = 0
                    if is_negation_gate(g):   # literal is ¬x
                        gamma[gid][0] = 0.0
                        delta[gid][0] = 1.0
                    else:                     # literal is x
                        gamma[gid][0] = 1.0
                        delta[gid][0] = 0.0
                else:
                    # var(g) = {y} and y != x => max_ell = 1
                    py = p[y]
                    ey = e[y]
                    if is_negation_gate(g):   # literal is ¬y
                        gamma[gid][0] = 1.0 - py
                        delta[gid][0] = 1.0 - py
                        gamma[gid][1] = 1.0 - ey
                        delta[gid][1] = 1.0 - ey
                    else:                     # literal is y
                        gamma[gid][0] = py
                        delta[gid][0] = py
                        gamma[gid][1] = ey
                        delta[gid][1] = ey

            elif g.is_decision():
                # SDD decision node: OR over elements (prime ∧ sub)

                # ---- Phase 1: AND (prime ∧ sub) ----
                per_child = []  # (child_gamma, child_delta, child_len)
                for prime, sub in g.elements():
                    pid = prime.id
                    sid = sub.id

                    Vp = var_of[pid] - {x}
                    Vs = var_of[sid] - {x}
                    Vc = Vp | Vs
                    Lp, Ls = len(Vp), len(Vs)
                    child_len = len(Vc)

                    child_gamma = [0.0] * (child_len + 1)
                    child_delta = [0.0] * (child_len + 1)

                    # decomposable AND, NO combinatorial weights
                    for ell_child in range(child_len + 1):
                        gsum = 0.0
                        dsum = 0.0
                        for ell_p in range(Lp + 1):
                            ell_s = ell_child - ell_p
                            if 0 <= ell_s <= Ls:
                                gsum += gamma[pid][ell_p] * gamma[sid][ell_s]
                                dsum += delta[pid][ell_p] * delta[sid][ell_s]
                        child_gamma[ell_child] = gsum
                        child_delta[ell_child] = dsum

                    per_child.append((child_gamma, child_delta, child_len))

                # ---- Phase 2: OR over elements ----
                # Each element may omit some vars; lift it to max_ell via binomial smoothing,
                # then sum across elements.
                for child_gamma, child_delta, child_len in per_child:
                    missing = max_ell - child_len  # >= 0
                    for ell_parent in range(max_ell + 1):
                        acc_g = 0.0
                        acc_d = 0.0
                        for ell_child in range(child_len + 1):
                            dist = ell_parent - ell_child
                            if 0 <= dist <= missing:
                                w = comb(missing, dist)
                                acc_g += child_gamma[ell_child] * w
                                acc_d += child_delta[ell_child] * w
                        gamma[gid][ell_parent] += acc_g
                        delta[gid][ell_parent] += acc_d

            else:
                raise NotImplementedError(f"Gate type not handled for node {g.id}")

        # Compute SHAP score for variable x
        shap_x = 0.0
        for k in range(n):
            weight = 1.0 if n == 1 else 1.0 / (n * comb(n - 1, k))
            term = (e[x] - p[x]) * (gamma[gout_id][k] - delta[gout_id][k])
            shap_x += weight * term

        shap_scores[x] = shap_x

    return shap_scores
    
def compute_shap_scores(sdd, marginals=None, entity=None, check=False, atol=1e-9, rtol=1e-7):
    """
    Compute SHAP scores for an SDD with given marginals and entity values.

    Args:
        sdd: SddNode root of the compiled circuit.
        marginals: dict mapping variable names (e.g., "x1") to marginal probabilities.
                   Defaults to 0.5 for any missing variable.
        entity: dict mapping variable names (e.g., "x1") to entity values (0 or 1).
                Defaults to 1 for any missing variable.
        check: if True, certify the returned SHAP scores by subset-enumeration
               (exact Shapley formula over all subsets) using shap_exact_subset_enum.
        atol, rtol: numeric tolerances for certification.

    Returns:
        dict mapping variable names to SHAP scores.
    """
    if sdd is None:
        raise ValueError("The SDD is None. Cannot compute SHAP scores.")

    mgr = sdd.manager
    var_count = mgr.var_count()
    var_ids = list(range(1, var_count + 1))
    var_id_to_name = {i: f"x{i}" for i in var_ids}

    if marginals is None:
        marginals = {}
    if entity is None:
        entity = {}

    p = {}
    e = {}
    for vid in var_ids:
        name = var_id_to_name[vid]
        p[vid] = float(marginals.get(name, 0.5))
        e[vid] = int(entity.get(name, 1))

    # Fast method
    shap_by_id = compute_shap_algorithm(sdd, p, e)

    # Optional certification via exact subset enumeration
    if check:
        brute_by_id = shap_exact_subset_enum(sdd, p, e, var_ids)

        diffs = {}
        for vid in var_ids:
            a = float(shap_by_id.get(vid, 0.0))
            b = float(brute_by_id.get(vid, 0.0))
            diff = abs(a - b)
            tol = atol + rtol * max(1.0, abs(b))
            if diff > tol:
                diffs[vid] = (a, b, diff, tol)

        if diffs:
            worst_vid = max(diffs, key=lambda k: diffs[k][2])
            a, b, diff, tol = diffs[worst_vid]
            name = var_id_to_name[worst_vid]
            raise AssertionError(
                f"SHAP certification failed for {name}: fast={a:.12g}, brute={b:.12g}, "
                f"|diff|={diff:.3g} > tol={tol:.3g}. "
                f"Mismatches: {len(diffs)}/{len(var_ids)}."
            )

    return {var_id_to_name[vid]: float(shap_by_id.get(vid, 0.0)) for vid in var_ids}


### Sanity Check ###
def v_conditional_wmc(sdd, p, e, S):
    """
    v(S) = E(C=1 | Z_S = e_S) under product marginals p.
    """
    wmc = sdd.wmc(log_mode=False)
    mgr = sdd.manager

    for i, pi in p.items():
        lit = mgr.literal(i)
        nlit = mgr.literal(-i)

        if i in S:
            if e[i] == 1:
                wmc.set_literal_weight(lit, 1.0)
                wmc.set_literal_weight(nlit, 0.0)
            else:
                wmc.set_literal_weight(lit, 0.0)
                wmc.set_literal_weight(nlit, 1.0)
        else:
            wmc.set_literal_weight(lit, pi)
            wmc.set_literal_weight(nlit, 1.0 - pi)

    return wmc.propagate()

def shap_exact_subset_enum(sdd, p, e, var_ids):
    n = len(var_ids)
    def w(k): return 1.0 if n == 1 else 1.0 / (n * comb(n - 1, k))

    # cache v(S)
    v = {}
    for r in range(n + 1):
        for S in itertools.combinations(var_ids, r):
            v[frozenset(S)] = v_conditional_wmc(sdd, p, e, set(S))

    phi = {}
    for x in var_ids:
        others = [i for i in var_ids if i != x]
        acc = 0.0
        for k in range(n):
            for S in itertools.combinations(others, k):
                S = set(S)
                acc += w(k) * (v[frozenset(S | {x})] - v[frozenset(S)])
        phi[x] = acc
    return phi
