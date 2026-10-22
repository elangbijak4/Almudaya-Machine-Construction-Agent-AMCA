import unittest
from dataclasses import replace

from amca.constructor import construct
from tests.support import reference_spec


class ConstructorTests(unittest.TestCase):
    def test_constructs_exact_six_nodes_and_six_edges(self):
        graph = construct(reference_spec())
        self.assertEqual(
            {node.id for node in graph.nodes},
            {"input", "validate", "analysis_a", "analysis_b", "aggregate", "report"},
        )
        self.assertEqual(len(graph.edges), 6)

    def test_node_and_edge_order_is_canonical(self):
        spec = reference_spec()
        reordered = replace(spec, nodes=tuple(reversed(spec.nodes)), edges=tuple(reversed(spec.edges)))
        left, right = construct(spec), construct(reordered)
        self.assertEqual(left.candidate_sha256, right.candidate_sha256)
        self.assertEqual(left.nodes, right.nodes)


if __name__ == "__main__":
    unittest.main()
