"""Stable deterministic topological scheduling."""
from __future__ import annotations

import heapq

from .errors import GraphError
from .models import CandidateGraph


def topological_order(candidate: CandidateGraph) -> tuple[str, ...]:
    ids = [node.id for node in candidate.nodes]
    if len(ids) != len(set(ids)):
        raise GraphError("Node ids must be unique before scheduling")
    known = set(ids)
    incoming = {node_id: 0 for node_id in ids}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in ids}
    for edge in candidate.edges:
        if edge.source not in known or edge.target not in known:
            raise GraphError("Edge endpoint does not exist", path=f"edges[{edge.source}->{edge.target}]")
        outgoing[edge.source].append(edge.target)
        incoming[edge.target] += 1
    ready = [node_id for node_id, count in incoming.items() if count == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        node_id = heapq.heappop(ready)
        order.append(node_id)
        for target in sorted(outgoing[node_id]):
            incoming[target] -= 1
            if incoming[target] == 0:
                heapq.heappush(ready, target)
    if len(order) != len(ids):
        raise GraphError("Candidate graph contains a cycle")
    return tuple(order)
