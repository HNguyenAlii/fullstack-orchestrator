from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = (
    REPO_ROOT / "fullstack-orchestrator" / "scripts" / "bootstrap_project_adapter.py"
)
BOOTSTRAP_SPEC = importlib.util.spec_from_file_location(
    "bootstrap_project_adapter", BOOTSTRAP_PATH
)
if BOOTSTRAP_SPEC is None or BOOTSTRAP_SPEC.loader is None:
    raise RuntimeError(f"Unable to load bootstrap from {BOOTSTRAP_PATH}")
BOOTSTRAP = importlib.util.module_from_spec(BOOTSTRAP_SPEC)
sys.modules[BOOTSTRAP_SPEC.name] = BOOTSTRAP
BOOTSTRAP_SPEC.loader.exec_module(BOOTSTRAP)


class ContractPrefixTests(unittest.TestCase):
    def test_prefix_is_derived_from_project_name(self) -> None:
        self.assertEqual(BOOTSTRAP.derive_contract_prefix("Alii"), "ALII")
        self.assertEqual(BOOTSTRAP.derive_contract_prefix("acme-shop"), "ACMESHOP")
        self.assertEqual(BOOTSTRAP.derive_contract_prefix("123"), "PRJ")

    def _bootstrap_slices(self, *extra_args: str) -> str:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            coordinator = root / "orc"
            subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP_PATH),
                    str(repo),
                    "--coordinator",
                    str(coordinator),
                    "--write",
                    *extra_args,
                ],
                check=True,
                capture_output=True,
            )
            return (coordinator / "SLICES.md").read_text()

    def test_generated_slices_use_project_prefix(self) -> None:
        slices = self._bootstrap_slices("--project-name", "Alii")

        self.assertIn("### ALII-001", slices)
        self.assertIn("`ALII-*`", slices)
        self.assertNotIn("BC-", slices)

    def test_explicit_contract_prefix_wins(self) -> None:
        slices = self._bootstrap_slices(
            "--project-name", "Alii", "--contract-prefix", "ali"
        )

        self.assertIn("### ALI-001", slices)


if __name__ == "__main__":
    unittest.main()
