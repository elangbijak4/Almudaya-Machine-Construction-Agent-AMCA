import unittest
from dataclasses import replace
from unittest.mock import patch

from amca.models import Edge, GraphNode
from amca.verifier import CHECK_IDS, verify_candidate
from tests.support import reference_graph


class VerifierTests(unittest.TestCase):
    def test_reference_graph_passes_every_mandatory_check(self):
        report = verify_candidate(reference_graph())
        self.assertEqual(report.status, "verified")
        self.assertEqual(tuple(check.id for check in report.checks), CHECK_IDS)
        self.assertTrue(all(check.status == "passed" for check in report.checks))

    def test_missing_dependency_and_unknown_endpoint_are_rejected(self):
        graph = reference_graph()
        missing = replace(graph, edges=tuple(edge for edge in graph.edges if not (edge.source == "analysis_b" and edge.target == "aggregate")))
        report = verify_candidate(missing)
        self.assertEqual(report.status, "rejected")
        self.assertIn("missing_required_input", {reason.code for reason in report.reasons})
        bad_edge = Edge("absent", "text", "report", "summary")
        report = verify_candidate(replace(graph, edges=graph.edges + (bad_edge,)))
        self.assertIn("unknown_endpoint", {reason.code for reason in report.reasons})

    def test_duplicate_node_unknown_component_and_cycle_are_rejected(self):
        graph = reference_graph()
        duplicate = GraphNode("input", "input_source", {"input_key": "text"})
        report = verify_candidate(replace(graph, nodes=graph.nodes + (duplicate,)))
        self.assertIn("duplicate_node_id", {reason.code for reason in report.reasons})
        changed = tuple(replace(node, component="unknown") if node.id == "analysis_a" else node for node in graph.nodes)
        report = verify_candidate(replace(graph, nodes=changed))
        self.assertIn("unknown_component", {reason.code for reason in report.reasons})
        report = verify_candidate(replace(graph, edges=graph.edges + (Edge("report", "report", "input", "text"),)))
        self.assertIn("cycle_detected", {reason.code for reason in report.reasons})

    def test_bad_ports_and_double_connections_are_rejected(self):
        graph = reference_graph()
        bad_port = tuple(
            replace(edge, output="missing") if edge.source == "validate" and edge.target == "analysis_a" else edge
            for edge in graph.edges
        )
        report = verify_candidate(replace(graph, edges=bad_port))
        self.assertIn("unknown_output_port", {reason.code for reason in report.reasons})
        extra = Edge("analysis_a", "finding", "aggregate", "finding_b")
        report = verify_candidate(replace(graph, edges=graph.edges + (extra,)))
        self.assertIn("duplicate_input_connection", {reason.code for reason in report.reasons})

    def test_incompatible_port_types_are_rejected(self):
        graph = reference_graph()
        edges = tuple(
            replace(edge, source="validate", output="text")
            if edge.source == "analysis_a" and edge.target == "aggregate"
            else edge
            for edge in graph.edges
        )
        report = verify_candidate(replace(graph, edges=edges))
        self.assertIn("incompatible_ports", {reason.code for reason in report.reasons})

    def test_invalid_node_identifier_is_rejected_even_for_direct_candidate(self):
        graph = reference_graph()
        nodes = tuple(replace(node, id="Not valid") if node.id == "analysis_a" else node for node in graph.nodes)
        report = verify_candidate(replace(graph, nodes=nodes))
        self.assertIn("invalid_node_id", {reason.code for reason in report.reasons})

    def test_profile_and_candidate_digest_are_bound(self):
        graph = reference_graph()
        report = verify_candidate(replace(graph, registry_profile="other"))
        self.assertIn("registry_profile_mismatch", {reason.code for reason in report.reasons})
        report = verify_candidate(replace(graph, candidate_sha256="f" * 64))
        self.assertIn("candidate_digest_mismatch", {reason.code for reason in report.reasons})

    def test_failed_check_yields_inconclusive(self):
        graph = reference_graph()
        with patch("amca.verifier._CHECKS", (("forced", lambda candidate: (_ for _ in ()).throw(RuntimeError())),)):
            report = verify_candidate(graph)
        self.assertEqual(report.status, "inconclusive")
        self.assertEqual(report.checks[0].status, "inconclusive")


if __name__ == "__main__":
    unittest.main()

