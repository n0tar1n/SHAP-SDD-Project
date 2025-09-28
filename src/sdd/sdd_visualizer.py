from pysdd.sdd import SddNode
from typing import Optional


def _format_sddnode_label(node, litnamemap=None):
    if litnamemap is None:
        litnamemap = {}  # Use an empty dictionary if no litnamemap is provided

    if node.is_true():
        return litnamemap.get("true", "⊤")
    elif node.is_false():
        return litnamemap.get("false", "⟘")
    elif node.is_literal():
        return litnamemap.get(node.literal, str(node.literal))
    else:
        return ""

# Recursive Dot Generator
def _sddnode_to_dot_int(node, visited, litnamemap, show_id, merge_leafs):
    # Check if the node has already been visited
    if node.id in visited:
        return node.id, []      # Avoid cycles in DAG

    visited.add(node.id)
    dot_lines = []

    # Handle terminal nodes (True/False or literals)
    if node.is_true() or node.is_false() or node.is_literal():
        label = _format_sddnode_label(node, litnamemap=litnamemap)
        dot_lines.append(f'{node.id} [label="{label}"];')
        return node.id, dot_lines

    # Handle decomposition nodes (AND/OR gates)
    for prime, sub in node.elements():
        prime_id, prime_lines = _sddnode_to_dot_int(prime, visited, litnamemap, show_id, merge_leafs)
        sub_id, sub_lines = _sddnode_to_dot_int(sub, visited, litnamemap, show_id, merge_leafs)
        dot_lines.extend(prime_lines)
        dot_lines.extend(sub_lines)
        dot_lines.append(f'{node.id} -> {prime_id};')
        dot_lines.append(f'{node.id} -> {sub_id};')

    return node.id, dot_lines


def sdd_to_dot(node, litnamemap=None, show_id=False, merge_leafs=False):
    visited = set()
    dot_lines = ["digraph SDD {"]
    nodeid, root_lines = _sddnode_to_dot_int(node, visited, litnamemap, show_id, merge_leafs)
    dot_lines.extend(root_lines)
    dot_lines.append("}")
    return "\n".join(dot_lines)