import ast
import unittest
from pathlib import Path

from amca.errors import SpecificationError
from amca.specification import load_spec
from tests.support import ROOT


class UntrustedSpecificationTests(unittest.TestCase):
    def test_code_and_command_strings_are_only_data_and_unknown_fields_reject(self):
        source = b"""
schema_version: '1.0'
machine_id: demo
nodes:
  - id: input
    component: input_source
    config:
      input_key: text
      command: \"__import__('os').system('whoami')\"
edges: []
"""
        with self.assertRaises(SpecificationError):
            load_spec(source)

    def test_dynamic_execution_and_process_launch_calls_are_absent(self):
        forbidden_calls = {"eval", "exec", "__import__"}
        forbidden_modules = {"subprocess", "importlib", "socket", "urllib", "http", "requests"}
        for path in (ROOT / "src" / "amca").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, forbidden_calls, str(path))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, {"system", "popen", "Popen", "spawn", "run"}, str(path))
                if isinstance(node, ast.Import):
                    self.assertFalse(any(alias.name in forbidden_modules for alias in node.names), str(path))
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, forbidden_modules, str(path))

    def test_unknown_component_name_is_rejected(self):
        source = b"""schema_version: '1.0'
machine_id: demo
nodes: [{id: run, component: os_system, config: {}}]
edges: []
"""
        with self.assertRaises(SpecificationError):
            load_spec(source)


if __name__ == "__main__":
    unittest.main()
