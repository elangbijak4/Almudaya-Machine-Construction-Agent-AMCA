import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT


class CliEndToEndTests(unittest.TestCase):
    def run_cli(self, *args):
        env = os.environ.copy()
        source = str(ROOT / "src")
        env["PYTHONPATH"] = source + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "amca.cli", *args],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_validate_verify_and_run_reference_graph(self):
        spec = "examples/valid_parallel_analysis.yaml"
        validation = self.run_cli("validate", spec)
        self.assertEqual(validation.returncode, 0, validation.stderr)
        self.assertEqual(json.loads(validation.stdout)["status"], "valid")
        verified = self.run_cli("verify", spec)
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["status"], "verified")
        result = self.run_cli("run", spec, "--inputs", "examples/reference-input.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["run_status"], "succeeded")
        self.assertEqual(record["node_records"][-1]["output_summary"]["value_type"], "object")

    def test_invalid_missing_dependency_is_rejected_without_execution(self):
        result = self.run_cli(
            "run",
            "examples/invalid_missing_dependency.yaml",
            "--inputs",
            "examples/reference-input.json",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["run_status"], "refused")
        self.assertEqual(record["verification"]["status"], "rejected")
        self.assertEqual(record["node_records"], [])

    def test_report_command_displays_json_report(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            result = self.run_cli(
                "verify",
                "examples/valid_parallel_analysis.yaml",
                "--output",
                str(report_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            displayed = self.run_cli("report", str(report_path))
            self.assertEqual(displayed.returncode, 0, displayed.stderr)
            self.assertEqual(json.loads(displayed.stdout)["status"], "verified")

    def test_duplicate_json_input_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "duplicate.json"
            input_path.write_text('{"text":"one","text":"two"}', encoding="utf-8")
            result = self.run_cli(
                "run",
                "examples/valid_parallel_analysis.yaml",
                "--inputs",
                str(input_path),
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("input_error", json.loads(result.stderr)["error"]["category"])

    def test_cyclic_candidate_is_rejected_before_runtime(self):
        source = (ROOT / "examples" / "valid_parallel_analysis.yaml").read_text(encoding="utf-8")
        source += '  - {from: "report", out: "report", to: "input", in: "text"}\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cycle.yaml"
            path.write_text(source, encoding="utf-8")
            result = self.run_cli("run", str(path), "--inputs", "examples/reference-input.json")
        self.assertEqual(result.returncode, 1, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["run_status"], "refused")
        self.assertEqual(record["verification"]["status"], "rejected")
        self.assertEqual(record["node_records"], [])


if __name__ == "__main__":
    unittest.main()

