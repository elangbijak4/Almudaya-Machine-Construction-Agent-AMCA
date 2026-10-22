import unittest

from amca.errors import SpecificationError
from amca.schema import validate_spec_mapping
from amca.specification import load_spec


def make_spec(node_count=1, edge_count=0):
    nodes = [
        {"id": f"n{i}", "component": "input_source", "config": {"input_key": "text"}}
        for i in range(node_count)
    ]
    edges = [
        {"from": "n0", "out": "text", "to": "n0", "in": f"p{i}"}
        for i in range(edge_count)
    ]
    return {"schema_version": "1.0", "machine_id": "limit-test", "nodes": nodes, "edges": edges}


class LimitTests(unittest.TestCase):
    def test_accepts_64_nodes_and_rejects_65(self):
        self.assertEqual(len(validate_spec_mapping(make_spec(64)).nodes), 64)
        with self.assertRaises(SpecificationError):
            validate_spec_mapping(make_spec(65))

    def test_accepts_128_edges_and_rejects_129(self):
        self.assertEqual(len(validate_spec_mapping(make_spec(1, 128)).edges), 128)
        with self.assertRaises(SpecificationError):
            validate_spec_mapping(make_spec(1, 129))

    def test_accepts_yaml_at_exact_byte_limit_and_rejects_one_over(self):
        base = b"schema_version: '1.0'\nmachine_id: demo\nnodes: [{id: input, component: input_source, config: {input_key: text}}]\nedges: []\n"
        padded = base + b" " * (65_536 - len(base))
        self.assertEqual(load_spec(padded).machine_id, "demo")
        with self.assertRaises(SpecificationError):
            load_spec(padded + b" ")


if __name__ == "__main__":
    unittest.main()
