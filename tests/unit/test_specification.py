import unittest

from amca.errors import InputError, SpecificationError
from amca.specification import load_spec


VALID = b"""
schema_version: '1.0'
machine_id: demo
nodes:
  - {id: input, component: input_source, config: {input_key: text}}
edges: []
"""


class SpecificationTests(unittest.TestCase):
    def test_loads_valid_single_document(self):
        spec = load_spec(VALID)
        self.assertEqual(spec.machine_id, "demo")
        self.assertEqual(spec.nodes[0].component, "input_source")

    def test_rejects_malformed_yaml(self):
        with self.assertRaises(InputError):
            load_spec(b"schema_version: [")

    def test_rejects_invalid_utf8(self):
        with self.assertRaises(InputError):
            load_spec(bytes([0xFF]))

    def test_rejects_empty_and_non_mapping_roots(self):
        for value in (b"", b"- one\n- two\n"):
            with self.subTest(value=value), self.assertRaises(SpecificationError):
                load_spec(value)

    def test_rejects_multiple_documents(self):
        with self.assertRaises(InputError):
            load_spec(VALID + b"---\nother: true\n")

    def test_rejects_duplicate_keys(self):
        with self.assertRaises(InputError):
            load_spec(b"schema_version: '1.0'\nschema_version: '1.0'\n")

    def test_rejects_aliases_and_anchors(self):
        with self.assertRaises(SpecificationError):
            load_spec(b"schema_version: &version '1.0'\nmachine_id: *version\n")

    def test_rejects_custom_tags(self):
        with self.assertRaises(InputError):
            load_spec(b"schema_version: !custom '1.0'\n")

    def test_rejects_oversized_yaml(self):
        with self.assertRaises(SpecificationError):
            load_spec(b"x" * 65_537)


if __name__ == "__main__":
    unittest.main()
