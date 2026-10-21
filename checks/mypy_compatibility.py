"""Check mypy's configured target and strictness, not package-wide typing."""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from mypy import api
from mypy.version import __version__


class MypyCompatibilityTests(unittest.TestCase):
    def check_code(self, source):
        config = Path(__file__).resolve().parents[1] / "pyproject.toml"
        with TemporaryDirectory() as cache:
            return api.run([
                "--config-file", str(config), "--no-incremental",
                "--cache-dir", cache, "-c", source,
            ])

    def test_python38_api_is_accepted_with_configured_target(self):
        output, errors, status = self.check_code(
            "def has_prefix(value: str) -> bool:\n"
            "    return value.startswith('prefix')\n")
        self.assertEqual(status, 0, output + errors)
        self.assertNotIn("python_version:", errors)

    def test_python39_only_api_is_rejected(self):
        output, errors, status = self.check_code(
            "def remove_prefix(value: str) -> str:\n"
            "    return value.removeprefix('prefix')\n")
        self.assertEqual(status, 1, output + errors)
        self.assertIn('has no attribute "removeprefix"', output)

    def test_config_still_rejects_untyped_definitions(self):
        output, errors, status = self.check_code(
            "def identity(value):\n    return value\n")
        self.assertEqual(status, 1, output + errors)
        self.assertIn("[no-untyped-def]", output)


if __name__ == "__main__":
    print("mypy {} on Python {}".format(__version__, sys.version.split()[0]))
    unittest.main()
