"""Guard user-facing PowerShell docs against malformed venv executable paths."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = [ROOT / "README.md", *sorted((ROOT / "help").glob("*.md"))]
BROKEN_VENV_PATH = re.compile(r"(?<!\.)\\\.venv\\Scripts\\python\.exe")


class WindowsCommandDocumentationTests(unittest.TestCase):
    def test_user_docs_do_not_omit_current_directory_prefix_before_venv(self):
        for path in DOCUMENTS:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(BROKEN_VENV_PATH.search(text), f"Malformed PowerShell path in {path}")

    def test_user_docs_show_the_correct_relative_venv_path(self):
        text = "\n".join(path.read_text(encoding="utf-8") for path in DOCUMENTS)
        self.assertIn(".\\.venv\\Scripts\\python.exe", text)


if __name__ == "__main__":
    unittest.main()
