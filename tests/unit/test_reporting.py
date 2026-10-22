import json
import unittest

from amca.reporting import serialize_report
from amca.verifier import verify_candidate
from tests.support import reference_graph


class ReportingTests(unittest.TestCase):
    def test_report_contains_check_and_reason_contract(self):
        value = verify_candidate(reference_graph()).as_dict()
        self.assertEqual(value["status"], "verified")
        self.assertTrue(value["checks"])
        self.assertTrue(all({"id", "status", "details"} <= set(check) for check in value["checks"]))
        self.assertEqual(json.loads(serialize_report(value))["candidate_sha256"], value["candidate_sha256"])

    def test_canonical_serialization_is_repeatable(self):
        report = verify_candidate(reference_graph())
        self.assertEqual(serialize_report(report), serialize_report(report))


if __name__ == "__main__":
    unittest.main()

