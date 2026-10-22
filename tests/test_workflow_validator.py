"""Smoke tests for the workflow validator itself (not for AMCA runtime)."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_workflow.py"

class WorkflowValidatorTests(unittest.TestCase):
    def run_validator(self, *args):
        return subprocess.run([sys.executable, str(VALIDATOR), *args], cwd=ROOT, capture_output=True, text=True)

    def test_scaffold_consistency_passes(self):
        result = self.run_validator("--check-scaffold")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validation: PASS", result.stdout)

    def test_owner_approved_p0_gate_passes(self):
        result = self.run_validator("--phase", "P0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_owner_approved_p1_gate_passes(self):
        result = self.run_validator("--phase", "P1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_owner_approved_p2_gate_passes(self):
        result = self.run_validator("--phase", "P2")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_owner_approved_p3_gate_passes(self):
        result = self.run_validator("--phase", "P3")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_owner_approved_p4_gate_passes(self):
        result = self.run_validator("--phase", "P4")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_owner_approved_p5_gate_passes(self):
        result = self.run_validator("--phase", "P5")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_owner_approved_p6_gate_passes(self):
        result = self.run_validator("--phase", "P6")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == "__main__":
    unittest.main()
