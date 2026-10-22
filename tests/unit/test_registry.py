import unittest

from amca.errors import SpecificationError
from amca.registry import component_ids, get_component


class RegistryTests(unittest.TestCase):
    def test_registry_contains_exact_allowlist(self):
        self.assertEqual(
            component_ids(),
            ("aggregate_results", "analysis_a", "analysis_b", "generate_report", "input_source", "validate_text"),
        )

    def test_unknown_component_is_rejected(self):
        with self.assertRaises(SpecificationError):
            get_component("os.system")

    def test_component_contracts_are_explicit(self):
        aggregate = get_component("aggregate_results")
        self.assertEqual(aggregate.input_ports, {"finding_a": "object", "finding_b": "object"})
        self.assertEqual(aggregate.output_ports, {"summary": "string"})


if __name__ == "__main__":
    unittest.main()
