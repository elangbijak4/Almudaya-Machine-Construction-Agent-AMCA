"""Graphviz source generation for verified AMCA candidate graphs."""
from __future__ import annotations

from amca.models import CandidateGraph


def to_dot(candidate: CandidateGraph) -> str:
    lines = ["digraph AMCA {", '  rankdir="LR";', '  graph [bgcolor="transparent", nodesep="0.55", ranksep="0.8"];',
             '  node [shape="box", style="rounded,filled", fillcolor="#eaf2ff", color="#3765a3", fontname="sans-serif"];',
             '  edge [color="#667085", fontname="sans-serif"];']
    for node in candidate.nodes:
        label = f"{node.id}\\n{node.component}"
        lines.append(f'  "{node.id}" [label="{label}"];')
    for edge in candidate.edges:
        lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{edge.output} → {edge.input}"];')
    lines.append("}")
    return "\n".join(lines)
