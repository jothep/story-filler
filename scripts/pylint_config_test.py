"""Check that Django-aware linting accepts valid models and rejects real errors."""

import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import unittest

REPOSITORY = Path(__file__).resolve().parents[1]
BACKEND = REPOSITORY / "backend"


class PylintConfigurationTests(unittest.TestCase):
    def run_pylint(self, source):
        with tempfile.TemporaryDirectory(prefix="story-filler-pylint-") as directory:
            fixture = Path(directory) / "lint_probe.py"
            fixture.write_text(source, encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                SECRET_KEY=secrets.token_urlsafe(48),
                DATABASE_URL="sqlite:///:memory:",
                USE_GCS="false",
                USE_S3="false",
                DEBUG="false",
            )
            paths = [str(BACKEND)]
            if environment.get("PYTHONPATH"):
                paths.append(environment["PYTHONPATH"])
            environment["PYTHONPATH"] = os.pathsep.join(paths)

            # Loading Django's model metadata needs settings, but no cloud
            # credentials, database records or production services.
            return subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pylint",
                    "--rcfile",
                    str(REPOSITORY / ".pylintrc"),
                    "--persistent=no",
                    str(fixture),
                ],
                cwd=BACKEND,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

    def test_django_fields_and_managers_are_understood(self):
        result = self.run_pylint(
            "from core.models import AppConfig, Story\n\n"
            "def inspect_models(story: Story, config: AppConfig):\n"
            "    return (\n"
            "        story.title.upper(),\n"
            "        config.updated_at.isoformat(),\n"
            "        Story.objects.all(),\n"
            "    )\n"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_error_blocks_high_scoring_code(self, source, message_id):
        # Keep the overall score above 7 so the test verifies fail-on=E,F,
        # rather than passing because this small fixture has a low score.
        constants = "".join(f"VALUE_{index:02d} = {index}\n" for index in range(50))
        result = self.run_pylint(source + "\n" + constants)
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn(message_id, output)
        score = re.search(r"rated at ([0-9.]+)/10", output)
        self.assertIsNotNone(score, output)
        self.assertGreaterEqual(float(score.group(1)), 7.0, output)

    def test_real_missing_model_member_is_rejected(self):
        self.assert_error_blocks_high_scoring_code(
            "from core.models import Story\n\n"
            "print(Story.this_attribute_does_not_exist)\n",
            "E1101",
        )

    def test_undefined_name_is_rejected(self):
        self.assert_error_blocks_high_scoring_code(
            "print(this_name_is_not_defined)\n", "E0602"
        )


if __name__ == "__main__":
    unittest.main()
