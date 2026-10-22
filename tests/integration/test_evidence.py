import unittest

from amca.runtime import run
from amca.verifier import verify_candidate
from tests.support import reference_graph


class EvidenceIntegrationTests(unittest.TestCase):
    def test_repeated_runs_have_same_deterministic_evidence(self):
        graph = reference_graph()
        verification = verify_candidate(graph)
        first = run(graph, verification, {"text": "AMCA builds a graph."})
        second = run(graph, verification, {"text": "AMCA builds a graph."})
        for key in ("candidate_sha256", "inputs_sha256", "verification", "run_status", "execution_order", "node_records"):
            self.assertEqual(first[key], second[key], key)

    def test_output_digests_and_sizes_are_recorded(self):
        graph = reference_graph()
        record = run(graph, verify_candidate(graph), {"text": "x"})
        for node in record["node_records"]:
            output = node["output_summary"]
            self.assertEqual(len(output["sha256"]), 64)
            self.assertGreaterEqual(output["byte_size"], 1)


if __name__ == "__main__":
    unittest.main()

