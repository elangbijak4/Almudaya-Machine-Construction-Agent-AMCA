import unittest

from amca.errors import SpecificationError
from amca.specification import load_spec


BASE = {
    "schema_version": "1.0",
    "machine_id": "demo",
    "nodes": [{"id": "input", "component": "input_source", "config": {"input_key": "text"}}],
    "edges": [],
}


class SchemaTests(unittest.TestCase):
    def test_rejects_missing_and_unknown_fields(self):
        for raw in (
            {key: value for key, value in BASE.items() if key != "edges"},
            {**BASE, "extra": True},
        ):
            with self.subTest(raw=raw), self.assertRaises(SpecificationError):
                from amca.schema import validate_spec_mapping
                validate_spec_mapping(raw)

    def test_rejects_wrong_types_and_version(self):
        cases = (
            {**BASE, "schema_version": 1.0},
            {**BASE, "nodes": {}},
            {**BASE, "machine_id": "Upper"},
            {**BASE, "nodes": [{"id": "bad id", "component": "input_source", "config": {"input_key": "text"}}]},
        )
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(SpecificationError):
                from amca.schema import validate_spec_mapping
                validate_spec_mapping(raw)

    def test_rejects_duplicate_node_ids(self):
        raw = {**BASE, "nodes": [BASE["nodes"][0], BASE["nodes"][0]]}
        from amca.schema import validate_spec_mapping
        with self.assertRaises(SpecificationError):
            validate_spec_mapping(raw)

    def test_rejects_unknown_components_and_config_keys(self):
        from amca.schema import validate_spec_mapping
        for node in (
            {"id": "x", "component": "unknown", "config": {}},
            {"id": "x", "component": "validate_text", "config": {"source": "code"}},
        ):
            with self.subTest(node=node), self.assertRaises(SpecificationError):
                validate_spec_mapping({**BASE, "nodes": [node]})

    def test_rejects_non_json_values(self):
        from amca.schema import validate_spec_mapping
        with self.assertRaises(SpecificationError):
            validate_spec_mapping({**BASE, "nodes": [{"id": "input", "component": "input_source", "config": {"input_key": "text", "value": float("nan")}}]})

    def test_rejects_unknown_edge_fields(self):
        raw = {**BASE, "edges": [{"from": "input", "out": "text", "to": "other", "in": "text", "extra": 1}]}
        from amca.schema import validate_spec_mapping
        with self.assertRaises(SpecificationError):
            validate_spec_mapping(raw)

    def test_rejects_too_many_nodes(self):
        nodes = [{"id": f"n{i}", "component": "validate_text", "config": {}} for i in range(65)]
        from amca.schema import validate_spec_mapping
        with self.assertRaises(SpecificationError):
            validate_spec_mapping({**BASE, "nodes": nodes})

    def test_rejects_oversized_config(self):
        from amca.schema import validate_spec_mapping
        node = {"id": "input", "component": "input_source", "config": {"input_key": "text", "x": "a" * 16_500}}
        with self.assertRaises(SpecificationError):
            validate_spec_mapping({**BASE, "nodes": [node]})

    def test_valid_spec_maps_to_models(self):
        spec = load_spec(b"schema_version: '1.0'\nmachine_id: demo\nnodes: [{id: input, component: input_source, config: {input_key: text}}]\nedges: []\n")
        self.assertEqual(spec.schema_version, "1.0")


if __name__ == "__main__":
    unittest.main()
