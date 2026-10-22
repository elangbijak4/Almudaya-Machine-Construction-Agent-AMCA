import unittest
from dataclasses import replace
from unittest.mock import patch

from amca.models import CandidateGraph
from amca.registry import _COMPONENTS
from amca.runtime import run
from amca.canonical import byte_size
from amca.verifier import verify_candidate
from tests.support import reference_graph


class RuntimeAdmissionTests(unittest.TestCase):
    def test_valid_graph_executes_real_registry_and_returns_evidence(self):
        graph = reference_graph()
        verification = verify_candidate(graph)
        record = run(graph, verification, {"text": "AMCA builds a graph."})
        self.assertEqual(record["run_status"], "succeeded")
        self.assertEqual(record["execution_order"], ["input", "validate", "analysis_a", "analysis_b", "aggregate", "report"])
        self.assertTrue(all(node["status"] == "succeeded" for node in record["node_records"]))
        self.assertEqual(record["node_records"][-1]["output_summary"]["value_type"], "object")
        self.assertEqual(
            record["node_records"][-1]["output_summary"]["safe_summary"],
            {"summary": "characters=20; words=4"},
        )
        self.assertNotIn("AMCA builds a graph.", str(record))

    def test_invalid_unknown_component_is_refused_before_any_invocation(self):
        graph = reference_graph()
        changed_nodes = tuple(replace(node, component="os.system") if node.id == "analysis_a" else node for node in graph.nodes)
        candidate = replace(graph, nodes=changed_nodes)
        calls = []
        original = _COMPONENTS["input_source"]
        with patch.dict(_COMPONENTS, {"input_source": replace(original, function=lambda config, values: calls.append("called") or original.function(config, values))}):
            record = run(candidate, verify_candidate(graph), {"text": "safe"})
        self.assertEqual(record["run_status"], "refused")
        self.assertEqual(calls, [])
        self.assertEqual(record["execution_order"], [])

    def test_stale_and_forged_verification_are_refused(self):
        graph = reference_graph()
        verified = verify_candidate(graph)
        changed = replace(graph, machine_id="changed")
        self.assertEqual(run(changed, verified, {"text": "safe"})["run_status"], "refused")
        forged = replace(verified, checks=())
        self.assertEqual(run(graph, forged, {"text": "safe"})["run_status"], "refused")

    def test_upstream_component_failure_skips_dependents(self):
        graph = reference_graph()
        record = run(graph, verify_candidate(graph), {"text": "   "})
        self.assertEqual(record["run_status"], "failed")
        self.assertEqual(record["execution_order"], ["input", "validate"])
        states = {node["node_id"]: node["status"] for node in record["node_records"]}
        self.assertEqual(states["validate"], "failed")
        self.assertEqual(states["aggregate"], "skipped")
        self.assertEqual(states["report"], "skipped")
        self.assertEqual(record["verification"]["status"], "verified")

    def test_missing_external_input_fails_before_component_execution(self):
        graph = reference_graph()
        from amca.errors import InputError
        with self.assertRaises(InputError):
            run(graph, verify_candidate(graph), {})

    def test_runtime_input_object_accepts_limit_and_rejects_one_over(self):
        graph = reference_graph()
        exact = {"text": "x" * 16_373}
        self.assertEqual(byte_size(exact), 16_384)
        self.assertEqual(run(graph, verify_candidate(graph), exact)["run_status"], "succeeded")
        over = {"text": "x" * 16_374}
        self.assertEqual(byte_size(over), 16_385)
        from amca.errors import InputError
        with self.assertRaises(InputError):
            run(graph, verify_candidate(graph), over)

    def test_oversized_component_output_fails_closed(self):
        graph = reference_graph()
        original = _COMPONENTS["generate_report"]
        oversized = replace(original, function=lambda config, values: {"report": {"summary": "x" * 65_530}})
        with patch.dict(_COMPONENTS, {"generate_report": oversized}):
            record = run(graph, verify_candidate(graph), {"text": "small"})
        self.assertEqual(record["run_status"], "failed")
        report_node = next(node for node in record["node_records"] if node["node_id"] == "report")
        self.assertEqual(report_node["status"], "failed")
        self.assertIn("exceeds 65,536", report_node["error"]["message"])

    def test_report_mismatch_cannot_be_used_as_runtime_authorization(self):
        graph = reference_graph()
        verified = verify_candidate(graph)
        mismatched = replace(verified, profile_id="forged-profile")
        record = run(graph, mismatched, {"text": "safe"})
        self.assertEqual(record["run_status"], "refused")
        self.assertEqual(record["node_records"], [])

    def test_direct_non_candidate_submission_is_refused(self):
        invalid = object()
        record = run(invalid, verify_candidate(invalid), {})
        self.assertEqual(record["run_status"], "refused")
        self.assertEqual(record["node_records"], [])


if __name__ == "__main__":
    unittest.main()

