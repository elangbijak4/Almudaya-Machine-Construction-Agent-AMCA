import unittest
from dataclasses import replace

from amca.errors import GraphError
from amca.models import Edge
from amca.scheduler import topological_order
from tests.support import reference_graph


class SchedulerTests(unittest.TestCase):
    def test_order_respects_dependencies_and_uses_stable_tie_break(self):
        order = topological_order(reference_graph())
        self.assertLess(order.index("input"), order.index("validate"))
        self.assertLess(order.index("validate"), order.index("analysis_a"))
        self.assertLess(order.index("analysis_a"), order.index("aggregate"))
        self.assertLess(order.index("analysis_b"), order.index("aggregate"))
        self.assertLess(order.index("analysis_a"), order.index("analysis_b"))

    def test_cycle_is_rejected(self):
        graph = reference_graph()
        cycle = Edge("report", "report", "input", "text")
        with self.assertRaises(GraphError):
            topological_order(replace(graph, edges=graph.edges + (cycle,)))

    def test_missing_endpoint_is_rejected(self):
        graph = reference_graph()
        bad = Edge("missing", "x", "report", "summary")
        with self.assertRaises(GraphError):
            topological_order(replace(graph, edges=graph.edges + (bad,)))


if __name__ == "__main__":
    unittest.main()
