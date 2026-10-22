"""End-to-end checks for the YAML-authoring CLI, with the model boundary stubbed."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from amca_agent import artifacts, cli


ROOT = Path(__file__).resolve().parents[2]
VALID = (ROOT / "examples" / "valid_parallel_analysis.yaml").read_text(encoding="utf-8")


class AgentCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.artifact_root = Path(self.temp.name) / "artifacts"
        self.patch_artifacts = mock.patch.object(artifacts, "ARTIFACT_ROOT", self.artifact_root)
        self.patch_cli_artifacts = mock.patch.object(cli, "ARTIFACT_ROOT", self.artifact_root)
        self.patch_artifacts.start()
        self.patch_cli_artifacts.start()
        self.addCleanup(self.patch_artifacts.stop)
        self.addCleanup(self.patch_cli_artifacts.stop)

    def invoke(self, *args: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = cli.main(list(args))
        return result, output.getvalue()

    def test_examples_copy_validation_and_graph_export(self):
        code, listed = self.invoke("examples")
        self.assertEqual(code, 0)
        self.assertIn("valid_parallel_analysis.yaml", listed)

        spec = Path(self.temp.name) / "machine.yaml"
        code, _ = self.invoke("example", "valid_parallel_analysis", "--output", str(spec))
        self.assertEqual(code, 0)
        code, report = self.invoke("validate", str(spec))
        self.assertEqual(code, 0)
        self.assertIn('"status": "verified"', report)

        graph = Path(self.temp.name) / "machine.dot"
        code, _ = self.invoke("graph", str(spec), "--output", str(graph))
        self.assertEqual(code, 0)
        self.assertIn("digraph AMCA", graph.read_text(encoding="utf-8"))

    def test_invalid_yaml_is_rejected_and_not_executed(self):
        invalid = ROOT / "examples" / "invalid_missing_dependency.yaml"
        code, message = self.invoke("validate", str(invalid))
        self.assertEqual(code, 1)
        self.assertIn('"status": "rejected"', message)
        self.assertFalse((self.artifact_root / "runs").exists())

    def test_noninteractive_run_persists_full_evidence(self):
        spec = Path(self.temp.name) / "machine.yaml"
        spec.write_text(VALID, encoding="utf-8")
        inputs = ROOT / "examples" / "reference-input.json"
        code, output = self.invoke("run", str(spec), "--inputs", str(inputs))
        self.assertEqual(code, 0)
        self.assertIn('"run_status": "succeeded"', output)
        folders = list((self.artifact_root / "runs").iterdir())
        self.assertEqual(len(folders), 1)
        self.assertTrue((folders[0] / "execution-record.json").is_file())
        self.assertTrue((folders[0] / "verification-report.json").is_file())
        code, shown = self.invoke("artifacts", "--show", folders[0].name)
        self.assertEqual(code, 0)
        self.assertIn("machine-dag.dot", shown)

    def test_chat_revisions_versions_restore_load_graph_run_and_session_reload(self):
        spec = Path(self.temp.name) / "edited.yaml"
        spec.write_text(VALID, encoding="utf-8")
        graph = Path(self.temp.name) / "chat.dot"
        inputs = ROOT / "examples" / "reference-input.json"
        commands = [
            "show", "validate", "revisi Pertahankan graph", "versions", "restore 1",
            f"load {spec}", f"graph {graph}", f"run {inputs}", "RUN", "quit",
        ]
        with mock.patch.object(cli, "_generate", return_value=VALID), mock.patch("builtins.input", side_effect=commands):
            code, output = self.invoke("chat", "--problem", "buat mesin contoh")
        self.assertEqual(code, 0)
        self.assertIn("Validasi: verified", output)
        self.assertIn("YAML dimuat sebagai versi v4", output)
        self.assertIn('"run_status": "succeeded"', output)
        self.assertTrue(graph.is_file())
        sessions = artifacts.list_sessions()
        self.assertEqual(len(sessions), 1)
        loaded = artifacts.load_chat(sessions[0])
        self.assertGreaterEqual(len(loaded["versions"]), 3)

        with mock.patch("builtins.input", side_effect=["quit"]):
            code, output = self.invoke("chat", "--session", loaded["session_id"])
        self.assertEqual(code, 0)
        self.assertIn("dimuat", output)


if __name__ == "__main__":
    unittest.main()
